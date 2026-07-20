import httpx
import pytest

from app.database.session import AsyncSessionLocal
from app.services.market_repository import count_candles
from app.tasks.historical_loader import run_historical_backfill


def _handler(request: httpx.Request) -> httpx.Response:
    if "exchangeInfo" in str(request.url):
        return httpx.Response(200, json={"symbols": [{"symbol": "BTCUSDT", "baseAsset": "BTC", "quoteAsset": "USDT"}]})

    limit = int(request.url.params.get("limit", 1500))
    end_time = request.url.params.get("endTime")
    end_time = int(end_time) if end_time else 1_700_100_000_000
    end_time = (end_time // 60_000) * 60_000

    rows = []
    for i in range(limit):
        open_time = end_time - (limit - 1 - i) * 60_000
        rows.append([open_time, "100", "101", "99", "100.5", "10", open_time + 59_999, "1000", 5, "5", "500", "0"])
    return httpx.Response(200, json=rows)


@pytest.fixture(autouse=True)
def mock_binance_rest_client(monkeypatch):
    import app.services.binance.rest_client as rc

    original_init = rc.BinanceRestClient.__init__

    def patched_init(self, base_url=None, timeout=10.0):
        original_init(self, base_url, timeout)
        self._client = httpx.AsyncClient(transport=httpx.MockTransport(_handler), base_url="https://fapi.binance.com")

    monkeypatch.setattr(rc.BinanceRestClient, "__init__", patched_init)


@pytest.mark.asyncio
async def test_backfill_reaches_target_count(db_session):
    await run_historical_backfill(AsyncSessionLocal, symbols=["BTCUSDT"], timeframes=["1m"], target_count=3200)

    count = await count_candles(db_session, "BTCUSDT", "1m")
    assert count == 3200


@pytest.mark.asyncio
async def test_backfill_is_idempotent_on_rerun(db_session):
    await run_historical_backfill(AsyncSessionLocal, symbols=["BTCUSDT"], timeframes=["1m"], target_count=2000)
    await run_historical_backfill(AsyncSessionLocal, symbols=["BTCUSDT"], timeframes=["1m"], target_count=2000)

    count = await count_candles(db_session, "BTCUSDT", "1m")
    assert count == 2000  # no duplicates from the second run


@pytest.mark.asyncio
async def test_backfill_registers_symbol_metadata(db_session):
    from sqlalchemy import select

    from app.models.symbol import Symbol

    await run_historical_backfill(AsyncSessionLocal, symbols=["BTCUSDT"], timeframes=["1m"], target_count=100)

    result = await db_session.execute(select(Symbol).where(Symbol.symbol == "BTCUSDT"))
    symbol_row = result.scalar_one()
    assert symbol_row.base_asset == "BTC"
    assert symbol_row.quote_asset == "USDT"
