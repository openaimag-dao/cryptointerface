import pytest
import pytest_asyncio

from app.core.redis import CANDLES_KEY, FUNDING_KEY, TICKER_KEY, cache_get_json, redis_client
from app.services.binance.parsers import AggTradeEvent, KlineEvent, MarkPriceEvent, MiniTickerEvent
from app.services.binance.rest_client import KlineData
from app.services.market_repository import bulk_upsert_candles, get_recent_candles
from app.tasks.live_feed import LiveFeedService


@pytest_asyncio.fixture(autouse=True)
async def clean_redis():
    await redis_client.flushdb()
    yield
    await redis_client.flushdb()


def make_service():
    broadcasts: list[tuple[str, dict]] = []

    async def broadcast(channel: str, payload: dict) -> None:
        broadcasts.append((channel, payload))

    service = LiveFeedService(symbols=["BTCUSDT"], timeframes=["1m"], broadcast=broadcast)
    return service, broadcasts


async def seed_history(db_session, symbol="BTCUSDT", interval="1m", count=260):
    klines = [
        KlineData(
            open_time=(1_700_000_000 + i * 60) * 1000,
            close_time=(1_700_000_059 + i * 60) * 1000,
            open=100 + i * 0.01,
            high=100.5 + i * 0.01,
            low=99.5 + i * 0.01,
            close=100.2 + i * 0.01,
            volume=10,
            quote_volume=1000,
            trades=5,
        )
        for i in range(count)
    ]
    await bulk_upsert_candles(db_session, symbol, interval, klines)


@pytest.mark.asyncio
async def test_in_progress_kline_only_caches_and_broadcasts(db_session):
    service, broadcasts = make_service()

    await service._handle_kline(
        KlineEvent(
            symbol="BTCUSDT",
            interval="1m",
            open_time=1_700_015_600_000,
            close_time=1_700_015_659_999,
            open=110,
            high=111,
            low=109,
            close=110.5,
            volume=5,
            quote_volume=500,
            trades=2,
            is_closed=False,
        )
    )

    assert [ch for ch, _ in broadcasts] == ["candle"]
    cached = await cache_get_json(CANDLES_KEY.format(symbol="BTCUSDT", interval="1m"))
    assert cached["close"] == 110.5

    count = len(await get_recent_candles(db_session, "BTCUSDT", "1m", limit=10))
    assert count == 0  # nothing persisted for an in-progress candle


@pytest.mark.asyncio
async def test_closed_kline_persists_and_broadcasts_indicators(db_session):
    await seed_history(db_session)
    service, broadcasts = make_service()

    await service._handle_kline(
        KlineEvent(
            symbol="BTCUSDT",
            interval="1m",
            open_time=1_700_015_600_000,
            close_time=1_700_015_659_999,
            open=110,
            high=111,
            low=109,
            close=110.5,
            volume=5,
            quote_volume=500,
            trades=2,
            is_closed=True,
        )
    )

    channels = [ch for ch, _ in broadcasts]
    assert "candle" in channels
    assert "indicators" in channels

    indicator_payload = next(payload for ch, payload in broadcasts if ch == "indicators")
    assert indicator_payload["symbol"] == "BTCUSDT"
    assert indicator_payload["ema"]["ema20"] is not None  # camelCase on the wire (Sprint 2 API convention)

    recent = await get_recent_candles(db_session, "BTCUSDT", "1m", limit=5)
    assert recent[-1].close == 110.5


@pytest.mark.asyncio
async def test_mark_price_caches_always_persists_only_on_funding_rollover(db_session):
    service, broadcasts = make_service()

    event_1 = MarkPriceEvent(
        symbol="BTCUSDT",
        mark_price=100.0,
        index_price=100.0,
        funding_rate=0.0001,
        next_funding_time=1_700_100_000_000,
        event_time=1_700_015_600_000,
    )
    event_2 = MarkPriceEvent(  # same funding period, price ticks
        symbol="BTCUSDT",
        mark_price=100.5,
        index_price=100.4,
        funding_rate=0.0001,
        next_funding_time=1_700_100_000_000,
        event_time=1_700_015_601_000,
    )
    event_3 = MarkPriceEvent(  # funding period rolled over
        symbol="BTCUSDT",
        mark_price=101.0,
        index_price=100.9,
        funding_rate=0.0002,
        next_funding_time=1_700_200_000_000,
        event_time=1_700_015_602_000,
    )

    await service._handle_mark_price(event_1)
    await service._handle_mark_price(event_2)
    await service._handle_mark_price(event_3)

    cached = await cache_get_json(FUNDING_KEY.format(symbol="BTCUSDT"))
    assert cached["mark_price"] == 101.0  # cache always reflects the latest tick

    from sqlalchemy import select

    from app.models.funding import FundingRate

    result = await db_session.execute(select(FundingRate).where(FundingRate.symbol == "BTCUSDT"))
    rows = result.scalars().all()
    assert len(rows) == 2  # only persisted on the initial tick + the funding rollover, not every tick


@pytest.mark.asyncio
async def test_mini_ticker_updates_cache_and_market_stats(db_session):
    service, broadcasts = make_service()

    await service._handle_mini_ticker(
        MiniTickerEvent(
            symbol="BTCUSDT",
            close=110.5,
            open=100.0,
            high=111,
            low=99,
            volume=1000,
            quote_volume=110000,
            event_time=1_700_015_600_000,
        )
    )

    cached = await cache_get_json(TICKER_KEY.format(symbol="BTCUSDT"))
    assert cached["price"] == 110.5
    assert cached["change_percent_24h"] == pytest.approx(10.5)

    from app.services.market_repository import get_market_stat

    stat = await get_market_stat(db_session, "BTCUSDT")
    assert stat is not None
    assert stat.price == 110.5


@pytest.mark.asyncio
async def test_agg_trade_only_broadcasts_no_persistence(db_session):
    service, broadcasts = make_service()

    await service._handle_agg_trade(
        AggTradeEvent(symbol="BTCUSDT", price=110.5, quantity=0.5, trade_time=1_700_015_600_500, is_buyer_maker=False)
    )

    assert [ch for ch, _ in broadcasts] == ["trade"]
