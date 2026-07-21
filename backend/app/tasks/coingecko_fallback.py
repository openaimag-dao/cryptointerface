"""Fallback live-ticker poller using CoinGecko's public REST API.

Binance stays the primary, real-time source (WebSocket) for everything.
This task only does anything when the Binance WebSocket is *not* fully
connected (e.g. this process's egress is geo-restricted from reaching
Binance) — it polls CoinGecko's `/coins/markets` on an interval so
`market_stats` (and the frontend's ticker) still move with real prices
instead of sitting stale, until Binance connectivity returns.

Deliberately narrow scope: price, 24h high/low/change/volume only. There
is no CoinGecko equivalent of funding rate or open interest (those are
futures-only concepts), and no WebSocket, so this can never fully replace
the Binance feed — it only keeps the ticker alive while Binance is down.
"""

import asyncio

from app.core.config import get_settings
from app.core.engine_state import engine_state
from app.core.logging import get_logger
from app.database.session import AsyncSessionLocal
from app.schemas.market import TickerUpdate
from app.services.coingecko.client import CoinGeckoRestClient
from app.services.coingecko.symbols import coingecko_id_for_symbol
from app.services.market_repository import upsert_market_stat

logger = get_logger(__name__)
settings = get_settings()

DEFAULT_POLL_INTERVAL_SECONDS = 45.0


async def poll_coingecko_fallback_once(
    client: CoinGeckoRestClient, id_by_symbol: dict[str, str], broadcast=None
) -> None:
    try:
        markets = await client.get_markets(list(id_by_symbol.values()))
    except Exception as exc:  # noqa: BLE001 — one bad poll must not kill the loop
        logger.warning("coingecko_fallback_poll_failed", extra={"error": str(exc)})
        return

    for symbol, coin_id in id_by_symbol.items():
        snapshot = markets.get(coin_id)
        if snapshot is None:
            continue

        async with AsyncSessionLocal() as db:
            await upsert_market_stat(
                db,
                symbol=symbol,
                price=snapshot.price,
                change_percent_24h=snapshot.change_percent_24h,
                high_24h=snapshot.high_24h,
                low_24h=snapshot.low_24h,
                volume_24h=snapshot.volume_24h,
                quote_volume_24h=snapshot.volume_24h * snapshot.price,
            )

        if broadcast:
            ticker_update = TickerUpdate(
                symbol=symbol,
                price=snapshot.price,
                change_percent_24h=snapshot.change_percent_24h,
                high_24h=snapshot.high_24h,
                low_24h=snapshot.low_24h,
                volume_24h=snapshot.volume_24h,
                quote_volume_24h=snapshot.volume_24h * snapshot.price,
            )
            await broadcast("ticker", ticker_update.model_dump(by_alias=True))

    logger.info("coingecko_fallback_poll_completed", extra={"symbols": list(id_by_symbol.keys())})


async def run_coingecko_fallback_poller(
    symbols: list[str] | None = None,
    interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
    broadcast=None,
    stop_event: asyncio.Event | None = None,
) -> None:
    symbols = symbols or settings.symbol_list
    stop_event = stop_event or asyncio.Event()

    id_by_symbol = {symbol: coin_id for symbol in symbols if (coin_id := coingecko_id_for_symbol(symbol)) is not None}
    if not id_by_symbol:
        logger.info("coingecko_fallback_disabled_no_mapped_symbols")
        return

    async with CoinGeckoRestClient() as client:
        while not stop_event.is_set():
            if engine_state.overall_ws_state != "connected":
                await poll_coingecko_fallback_once(client, id_by_symbol, broadcast)

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
            except TimeoutError:
                pass  # normal: just means it's time to check again
