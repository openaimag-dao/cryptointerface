from datetime import UTC, datetime

import numpy as np
import pytest

from app.intelligence.sentiment.engine import CATEGORY_WEIGHTS, compute_sentiment
from app.intelligence.sentiment.liquidation_factor import score_liquidations
from app.services.binance.rest_client import KlineData
from app.services.market_repository import insert_liquidation, upsert_candle


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
async def test_compute_sentiment_returns_none_without_candle_history(db_session):
    result = await compute_sentiment(db_session, "NOSUCHUSDT", "1h")
    assert result is None


@pytest.mark.asyncio
async def test_compute_sentiment_blends_all_five_categories(db_session):
    await _insert_candles(db_session, "TESTUSDT")

    result = await compute_sentiment(db_session, "TESTUSDT", "1h")

    assert result is not None
    assert set(result.breakdown.keys()) == {"technical", "macro", "liquidations", "news", "whales"}
    assert 0.0 <= result.overall_score <= 100.0
    assert 0.0 <= result.confidence <= 100.0
    assert result.direction in ("LONG", "SHORT", "WAIT")
    # No news articles or whale-covered-symbol data seeded in this test's
    # DB — both categories correctly read neutral/zero-confidence, but
    # both now carry real weight (unlike the old Sprint 4 stubs).
    assert result.breakdown["news"].confidence == 0.0
    assert result.breakdown["whales"].confidence == 0.0
    assert CATEGORY_WEIGHTS["whales"] > 0.0


@pytest.mark.asyncio
async def test_compute_sentiment_deterministic_same_input_same_output(db_session):
    await _insert_candles(db_session, "TESTUSDT")

    first = await compute_sentiment(db_session, "TESTUSDT", "1h")
    second = await compute_sentiment(db_session, "TESTUSDT", "1h")

    assert first is not None and second is not None
    assert first.overall_score == second.overall_score
    assert first.direction == second.direction


@pytest.mark.asyncio
async def test_compute_sentiment_reflects_heavy_long_liquidations(db_session):
    await _insert_candles(db_session, "TESTUSDT")
    recent_ms = int(datetime.now(UTC).timestamp() * 1000)
    for _ in range(5):
        await insert_liquidation(
            db_session,
            symbol="TESTUSDT",
            side="LONG",
            price=100.0,
            quantity=100.0,
            amount_usd=1_000_000.0,
            timestamp=recent_ms,
        )

    result = await compute_sentiment(db_session, "TESTUSDT", "1h")

    assert result is not None
    assert result.breakdown["liquidations"].score > 50.0
    assert any("capitulation" in reason for reason in result.breakdown["liquidations"].reasons)


def test_score_liquidations_thin_volume_is_neutral():
    factor = score_liquidations({"LONG": 1_000.0, "SHORT": 500.0})
    assert factor.score == 50.0


def test_score_liquidations_short_dominant_is_bearish():
    factor = score_liquidations({"LONG": 100_000.0, "SHORT": 2_000_000.0})
    assert factor.score < 50.0
    assert factor.direction in ("SHORT", "WAIT")
