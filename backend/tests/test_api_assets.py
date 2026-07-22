"""Router-level (HTTP) tests for app/api/assets.py — status codes, 404
branches, and interval validation, complementing the service-level
coverage already in test_asset_service.py (which never goes through
FastAPI/HTTP at all).
"""

import numpy as np
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.assets import router as assets_router
from app.database.session import get_db
from app.services.binance.rest_client import KlineData
from app.services.market_repository import upsert_candle, upsert_market_stat


def _app(db_session):
    app = FastAPI()
    app.include_router(assets_router)

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    return app


async def _client(db_session):
    transport = ASGITransport(app=_app(db_session))
    return AsyncClient(transport=transport, base_url="http://test")


async def _insert_candles(db_session, symbol: str, n: int = 260) -> None:
    base_time = 1_700_000_000_000
    closes = np.linspace(100, 160, n) + np.sin(np.linspace(0, 20, n)) * 0.5
    for i in range(n):
        kline = KlineData(
            open_time=base_time + i * 3_600_000,
            close_time=base_time + i * 3_600_000 + 3_599_999,
            open=float(closes[i]),
            high=float(closes[i]) + 0.5,
            low=float(closes[i]) - 0.5,
            close=float(closes[i]),
            volume=1_000.0,
            quote_volume=100_000.0,
            trades=50,
        )
        await upsert_candle(db_session, symbol, "1h", kline, is_closed=True)


@pytest.mark.asyncio
async def test_get_asset_summary_404_without_market_stat(db_session):
    async with await _client(db_session) as client:
        response = await client.get("/api/assets/NOPE")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_asset_summary_200_with_market_stat(db_session):
    await upsert_market_stat(db_session, "TESTUSDT", 150.0, 2.5, 155.0, 145.0, 1_000_000.0, 150_000_000.0)

    async with await _client(db_session) as client:
        response = await client.get("/api/assets/TEST")

    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "TESTUSDT"
    assert body["price"] == 150.0
    # response_model=AssetSummaryOut uses CamelModel -> camelCase keys on the wire.
    assert "changePercent24h" in body


@pytest.mark.asyncio
async def test_get_asset_summary_accepts_bare_asset_and_trading_pair(db_session):
    await upsert_market_stat(db_session, "TESTUSDT", 150.0, 2.5, 155.0, 145.0, 1_000_000.0, 150_000_000.0)

    async with await _client(db_session) as client:
        bare = await client.get("/api/assets/TEST")
        pair = await client.get("/api/assets/TESTUSDT")

    assert bare.status_code == pair.status_code == 200
    assert bare.json()["symbol"] == pair.json()["symbol"] == "TESTUSDT"


@pytest.mark.asyncio
async def test_get_asset_summary_rejects_unsupported_interval(db_session):
    async with await _client(db_session) as client:
        response = await client.get("/api/assets/TEST", params={"interval": "3x"})

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_asset_overview_404_without_candles(db_session):
    async with await _client(db_session) as client:
        response = await client.get("/api/assets/NOPE/overview")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_asset_overview_200_includes_new_market_snapshot_fields(db_session):
    await _insert_candles(db_session, "TESTUSDT")

    async with await _client(db_session) as client:
        response = await client.get("/api/assets/TEST/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["volumeTrend"]["name"] == "Volume Trend"
    assert body["liquidityScore"]["name"] == "Liquidity Score"


@pytest.mark.asyncio
async def test_get_asset_technical_returns_eight_smart_money_concepts(db_session):
    await _insert_candles(db_session, "TESTUSDT")

    async with await _client(db_session) as client:
        response = await client.get("/api/assets/TEST/technical")

    assert response.status_code == 200
    body = response.json()
    assert len(body["smartMoney"]) == 8
    assert all(c["status"] != "NOT_YET_IMPLEMENTED" for c in body["smartMoney"])


@pytest.mark.asyncio
async def test_get_asset_derivatives_includes_exchange_breakdown(db_session):
    async with await _client(db_session) as client:
        response = await client.get("/api/assets/TEST/derivatives")

    assert response.status_code == 200
    body = response.json()
    assert body["exchangeBreakdown"][0]["exchange"] == "Binance"
    assert body["exchangeBreakdown"][0]["status"] == "AVAILABLE"
    assert any(e["status"] == "NOT_YET_IMPLEMENTED" for e in body["exchangeBreakdown"][1:])


@pytest.mark.asyncio
async def test_get_asset_timeline_empty_list_without_analysis(db_session):
    async with await _client(db_session) as client:
        response = await client.get("/api/assets/NOPE/timeline")

    assert response.status_code == 200
    assert response.json()["entries"] == []


@pytest.mark.asyncio
async def test_get_asset_correlation_200_without_history(db_session):
    async with await _client(db_session) as client:
        response = await client.get("/api/assets/NOPE/correlation")

    assert response.status_code == 200
    readings = response.json()
    assert len(readings) > 0
    assert all(r["coefficient"] is None for r in readings)
