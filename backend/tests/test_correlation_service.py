import pytest

from app.services.binance.rest_client import KlineData
from app.services.correlation_service import (
    CORRELATION_MIN_DATA_POINTS,
    compute_correlations,
)
from app.services.macro_repository import insert_macro_point
from app.services.market_repository import bulk_upsert_candles


async def _seed_candles(db_session, symbol: str, closes: list[float], start_time_ms: int = 1_700_000_000_000) -> None:
    klines = [
        KlineData(
            open_time=start_time_ms + i * 3_600_000,
            close_time=start_time_ms + i * 3_600_000 + 3_599_999,
            open=c,
            high=c + 0.5,
            low=c - 0.5,
            close=c,
            volume=1000.0,
            quote_volume=100_000.0,
            trades=10,
        )
        for i, c in enumerate(closes)
    ]
    await bulk_upsert_candles(db_session, symbol, "1h", klines)


@pytest.mark.asyncio
async def test_compute_correlations_returns_none_with_no_data(db_session):
    readings = await compute_correlations(db_session, "NODATAUSDT", "1h")
    by_ref = {r.reference: r for r in readings}

    assert by_ref["BTC"].coefficient is None
    assert by_ref["BTC"].data_points == 0
    assert by_ref["NASDAQ"].coefficient is None


@pytest.mark.asyncio
async def test_compute_correlations_perfectly_correlated_series(db_session):
    n = CORRELATION_MIN_DATA_POINTS + 10
    closes = [100.0 + i for i in range(n)]  # steady uptrend
    await _seed_candles(db_session, "TESTUSDT", closes)
    await _seed_candles(db_session, "BTCUSDT", closes)  # identical series -> perfect correlation

    readings = await compute_correlations(db_session, "TESTUSDT", "1h")
    btc_reading = next(r for r in readings if r.reference == "BTC")

    assert btc_reading.coefficient is not None
    assert btc_reading.coefficient > 0.99
    assert btc_reading.data_points >= CORRELATION_MIN_DATA_POINTS


@pytest.mark.asyncio
async def test_compute_correlations_inversely_correlated_series(db_session):
    n = CORRELATION_MIN_DATA_POINTS + 10
    # A varying returns sequence, then a second series built from the
    # exact negative of those same returns each step — guarantees the two
    # return series are perfectly (Pearson -1) inversely related,
    # regardless of the raw price levels.
    step_returns = [0.01 if i % 3 else -0.02 for i in range(n)]
    up = [100.0]
    down = [100.0]
    for r in step_returns:
        up.append(up[-1] * (1 + r))
        down.append(down[-1] * (1 - r))

    await _seed_candles(db_session, "TESTUSDT", up)
    await _seed_candles(db_session, "ETHUSDT", down)

    readings = await compute_correlations(db_session, "TESTUSDT", "1h")
    eth_reading = next(r for r in readings if r.reference == "ETH")

    assert eth_reading.coefficient is not None
    assert eth_reading.coefficient < -0.99


@pytest.mark.asyncio
async def test_compute_correlations_below_min_data_points_returns_none(db_session):
    n = CORRELATION_MIN_DATA_POINTS - 5
    closes = [100.0 + i for i in range(n)]
    await _seed_candles(db_session, "TESTUSDT", closes)
    await _seed_candles(db_session, "BTCUSDT", closes)

    readings = await compute_correlations(db_session, "TESTUSDT", "1h")
    btc_reading = next(r for r in readings if r.reference == "BTC")

    assert btc_reading.coefficient is None


@pytest.mark.asyncio
async def test_compute_correlations_never_correlates_symbol_against_itself(db_session):
    closes = [100.0 + i for i in range(CORRELATION_MIN_DATA_POINTS + 10)]
    await _seed_candles(db_session, "BTCUSDT", closes)

    readings = await compute_correlations(db_session, "BTCUSDT", "1h")
    references = {r.reference for r in readings}

    assert "BTC" not in references
    assert "ETH" in references


@pytest.mark.asyncio
async def test_compute_correlations_macro_reference_with_enough_history(db_session):
    n = CORRELATION_MIN_DATA_POINTS + 10
    closes = [100.0 + i for i in range(n)]
    await _seed_candles(db_session, "TESTUSDT", closes)

    for i in range(n):
        await insert_macro_point(
            db_session,
            indicator="nasdaq",
            value=400.0 + i,
            source="test",
            fetched_at=1_700_000_000 + i * 3600,
        )

    readings = await compute_correlations(db_session, "TESTUSDT", "1h")
    nasdaq_reading = next(r for r in readings if r.reference == "NASDAQ")

    assert nasdaq_reading.coefficient is not None
    assert nasdaq_reading.data_points > 0


@pytest.mark.asyncio
async def test_compute_correlations_deterministic_same_input_same_output(db_session):
    n = CORRELATION_MIN_DATA_POINTS + 10
    closes = [100.0 + (i % 7) * 1.3 for i in range(n)]
    await _seed_candles(db_session, "TESTUSDT", closes)
    await _seed_candles(db_session, "BTCUSDT", [c * 1.5 for c in closes])

    first = await compute_correlations(db_session, "TESTUSDT", "1h")
    second = await compute_correlations(db_session, "TESTUSDT", "1h")

    assert [r.coefficient for r in first] == [r.coefficient for r in second]
