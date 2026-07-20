"""Consumes the live Binance WebSocket stream and fans it out:

kline (closed)   -> persist candle, recompute indicators, cache, broadcast
kline (in-progress) -> cache + broadcast only (no DB write, no indicator recompute)
markPrice         -> cache funding/mark price; persist only when the funding period rolls over
miniTicker        -> cache + persist 24h stats, broadcast ticker update
aggTrade          -> cache last trade price, broadcast a lightweight trade tick

This keeps the DB write rate bounded regardless of tick frequency, while
Redis (the hot-path cache) is updated on every message.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from app.core.config import get_settings
from app.core.engine_state import engine_state
from app.core.logging import get_logger
from app.core.redis import CANDLES_KEY, FUNDING_KEY, TICKER_KEY, cache_get_json, cache_set_json
from app.database.session import AsyncSessionLocal
from app.schemas.candle import Candle as CandleSchema
from app.schemas.candle import CandleUpdate
from app.schemas.funding import FundingRate
from app.schemas.market import TickerUpdate
from app.schemas.trade import TradeUpdate
from app.services.binance.parsers import AggTradeEvent, KlineEvent, MarkPriceEvent, MiniTickerEvent, StreamEvent
from app.services.binance.ws_client import BinanceWebSocketClient, ConnectionState
from app.services.indicators.engine import compute_indicators
from app.services.market_repository import (
    get_recent_candles,
    insert_funding,
    to_candle_schema,
    upsert_candle,
    upsert_indicator_value,
    upsert_market_stat,
)

logger = get_logger(__name__)
settings = get_settings()

BroadcastFn = Callable[[str, dict[str, Any]], Awaitable[None]]
StateChangeFn = Callable[[int, ConnectionState], Awaitable[None]]

INDICATOR_WARMUP_CANDLES = 250  # enough history for EMA200/ADX/etc to leave their warm-up window


class LiveFeedService:
    def __init__(
        self,
        symbols: list[str] | None = None,
        timeframes: list[str] | None = None,
        broadcast: BroadcastFn | None = None,
        on_state_change: StateChangeFn | None = None,
    ) -> None:
        self._symbols = symbols or settings.symbol_list
        self._timeframes = timeframes or settings.timeframe_list
        self._broadcast = broadcast
        self._on_state_change = on_state_change
        self._ws_client: BinanceWebSocketClient | None = None

    async def start(self) -> None:
        self._ws_client = BinanceWebSocketClient(
            symbols=self._symbols,
            timeframes=self._timeframes,
            on_event=self._handle_event,
            on_state_change=self._on_state_change,
        )
        logger.info("live_feed_starting", extra={"symbols": self._symbols, "timeframes": self._timeframes})
        await self._ws_client.start()

    async def stop(self) -> None:
        if self._ws_client:
            await self._ws_client.stop()

    async def _publish(self, channel: str, payload: dict[str, Any]) -> None:
        if self._broadcast:
            await self._broadcast(channel, payload)

    async def _handle_event(self, event: StreamEvent) -> None:
        if isinstance(event, KlineEvent):
            await self._handle_kline(event)
        elif isinstance(event, MarkPriceEvent):
            await self._handle_mark_price(event)
        elif isinstance(event, MiniTickerEvent):
            await self._handle_mini_ticker(event)
        elif isinstance(event, AggTradeEvent):
            await self._handle_agg_trade(event)

    async def _handle_kline(self, event: KlineEvent) -> None:
        engine_state.mark_kline(event.symbol)
        candle_payload = {
            "time": event.open_time // 1000,
            "open": event.open,
            "high": event.high,
            "low": event.low,
            "close": event.close,
            "volume": event.volume,
        }
        await cache_set_json(CANDLES_KEY.format(symbol=event.symbol, interval=event.interval), candle_payload)
        candle_update = CandleUpdate(
            symbol=event.symbol,
            interval=event.interval,
            candle=CandleSchema(**candle_payload),
            is_closed=event.is_closed,
        )
        await self._publish("candle", candle_update.model_dump(by_alias=True))

        if not event.is_closed:
            return  # only persist + recompute indicators on a *closed* candle

        async with AsyncSessionLocal() as db:
            await upsert_candle(db, event.symbol, event.interval, _kline_event_to_kline_data(event), is_closed=True)
            recent = await get_recent_candles(db, event.symbol, event.interval, limit=INDICATOR_WARMUP_CANDLES)
            if not recent:
                return
            snapshot = compute_indicators(event.symbol, event.interval, [to_candle_schema(c) for c in recent])
            await upsert_indicator_value(db, snapshot)

        await self._publish("indicators", snapshot.model_dump(by_alias=True))
        logger.info("candle_closed", extra={"symbol": event.symbol, "interval": event.interval, "close": event.close})

    async def _handle_mark_price(self, event: MarkPriceEvent) -> None:
        engine_state.mark_funding(event.symbol)
        payload = {
            "symbol": event.symbol,
            "funding_rate": event.funding_rate,
            "mark_price": event.mark_price,
            "funding_time": event.event_time,
            "next_funding_time": event.next_funding_time,
        }
        cache_key = FUNDING_KEY.format(symbol=event.symbol)
        previous = await cache_get_json(cache_key)
        await cache_set_json(cache_key, payload)
        funding_update = FundingRate(
            symbol=event.symbol,
            funding_rate=event.funding_rate,
            mark_price=event.mark_price,
            funding_time=event.event_time,
            next_funding_time=event.next_funding_time,
        )
        await self._publish("funding", funding_update.model_dump(by_alias=True))

        funding_period_changed = previous is None or previous.get("next_funding_time") != event.next_funding_time
        if funding_period_changed:
            async with AsyncSessionLocal() as db:
                await insert_funding(
                    db,
                    symbol=event.symbol,
                    funding_rate=event.funding_rate,
                    mark_price=event.mark_price,
                    funding_time=event.event_time,
                )

    async def _handle_mini_ticker(self, event: MiniTickerEvent) -> None:
        change_percent = ((event.close - event.open) / event.open * 100) if event.open else 0.0
        payload = {
            "symbol": event.symbol,
            "price": event.close,
            "change_percent_24h": change_percent,
            "high_24h": event.high,
            "low_24h": event.low,
            "volume_24h": event.volume,
            "quote_volume_24h": event.quote_volume,
        }
        await cache_set_json(TICKER_KEY.format(symbol=event.symbol), payload)
        ticker_update = TickerUpdate(
            symbol=event.symbol,
            price=event.close,
            change_percent_24h=change_percent,
            high_24h=event.high,
            low_24h=event.low,
            volume_24h=event.volume,
            quote_volume_24h=event.quote_volume,
        )
        await self._publish("ticker", ticker_update.model_dump(by_alias=True))

        async with AsyncSessionLocal() as db:
            await upsert_market_stat(
                db,
                symbol=event.symbol,
                price=event.close,
                change_percent_24h=change_percent,
                high_24h=event.high,
                low_24h=event.low,
                volume_24h=event.volume,
                quote_volume_24h=event.quote_volume,
            )

    async def _handle_agg_trade(self, event: AggTradeEvent) -> None:
        engine_state.mark_trade(event.symbol)
        trade_update = TradeUpdate(
            symbol=event.symbol,
            price=event.price,
            quantity=event.quantity,
            trade_time=event.trade_time,
            is_buyer_maker=event.is_buyer_maker,
        )
        await self._publish("trade", trade_update.model_dump(by_alias=True))


def _kline_event_to_kline_data(event: KlineEvent):
    from app.services.binance.rest_client import KlineData

    return KlineData(
        open_time=event.open_time,
        close_time=event.close_time,
        open=event.open,
        high=event.high,
        low=event.low,
        close=event.close,
        volume=event.volume,
        quote_volume=event.quote_volume,
        trades=event.trades,
    )
