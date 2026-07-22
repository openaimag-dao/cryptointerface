import numpy as np
import pytest

from app.ai_engine.indicator_explain import explain_indicators
from app.schemas.indicator import (
    BollingerBandsValues,
    EmaValues,
    IndicatorSnapshot,
    MacdValues,
    PivotLevels,
    StochRsiValues,
)


def _snapshot(**overrides) -> IndicatorSnapshot:
    defaults = dict(
        symbol="TESTUSDT",
        interval="1h",
        time=1_700_000_000,
        ema=EmaValues(ema_20=100.0, ema_50=95.0, ema_100=90.0, ema_200=80.0),
        rsi_14=55.0,
        macd=MacdValues(macd=1.0, signal=0.5, histogram=0.5),
        atr_14=1.0,
        bollinger_bands=BollingerBandsValues(upper=110.0, middle=100.0, lower=90.0),
        vwap=95.0,
        adx_14=30.0,
        obv=1000.0,
        stoch_rsi=StochRsiValues(k=50.0, d=45.0),
        pivot=PivotLevels(pivot=95.0, r1=105.0, r2=None, r3=None, s1=90.0, s2=None, s3=None),
    )
    defaults.update(overrides)
    return IndicatorSnapshot(**defaults)


def _by_name(readings):
    return {r.name: r for r in readings}


def test_explain_indicators_bullish_price_above_everything():
    closes = np.array([80.0, 90.0, 101.0])
    volumes = np.array([10.0, 10.0, 10.0])
    readings = _by_name(explain_indicators(_snapshot(), closes, volumes))

    assert readings["EMA20"].status == "BULLISH"
    assert readings["EMA Alignment"].status == "BULLISH"
    assert readings["VWAP"].status == "BULLISH"
    assert readings["Pivot Point"].status == "BULLISH"


def test_explain_indicators_bearish_price_below_everything():
    snapshot = _snapshot(ema=EmaValues(ema_20=80.0, ema_50=90.0, ema_100=95.0, ema_200=100.0))
    closes = np.array([120.0, 110.0, 70.0])
    volumes = np.array([10.0, 10.0, 10.0])
    readings = _by_name(explain_indicators(snapshot, closes, volumes))

    assert readings["EMA20"].status == "BEARISH"
    assert readings["EMA Alignment"].status == "BEARISH"
    assert readings["VWAP"].status == "BEARISH"
    assert readings["Pivot Point"].status == "BEARISH"


def test_explain_indicators_mixed_ema_alignment_is_neutral():
    snapshot = _snapshot(ema=EmaValues(ema_20=95.0, ema_50=100.0, ema_100=90.0, ema_200=80.0))
    closes = np.array([90.0, 95.0, 96.0])
    volumes = np.array([10.0, 10.0, 10.0])
    readings = _by_name(explain_indicators(snapshot, closes, volumes))

    assert readings["EMA Alignment"].status == "NEUTRAL"


@pytest.mark.parametrize(
    ("rsi", "expected_status"),
    [(75.0, "OVERBOUGHT"), (10.0, "OVERSOLD"), (60.0, "BULLISH"), (40.0, "BEARISH")],
)
def test_rsi_reading_status(rsi, expected_status):
    snapshot = _snapshot(rsi_14=rsi)
    closes = np.array([100.0])
    volumes = np.array([10.0])
    readings = _by_name(explain_indicators(snapshot, closes, volumes))

    assert readings["RSI (14)"].status == expected_status


def test_rsi_reading_missing_value_is_neutral_with_placeholder():
    snapshot = _snapshot(rsi_14=None)
    closes = np.array([100.0])
    volumes = np.array([10.0])
    readings = _by_name(explain_indicators(snapshot, closes, volumes))

    assert readings["RSI (14)"].status == "NEUTRAL"
    assert readings["RSI (14)"].value == "—"


@pytest.mark.parametrize(
    ("histogram", "expected_status"),
    [(0.5, "BULLISH"), (-0.5, "BEARISH"), (0.0, "NEUTRAL")],
)
def test_macd_reading_status_from_histogram_sign(histogram, expected_status):
    snapshot = _snapshot(macd=MacdValues(macd=1.0, signal=1.0 - histogram, histogram=histogram))
    closes = np.array([100.0])
    volumes = np.array([10.0])
    readings = _by_name(explain_indicators(snapshot, closes, volumes))

    assert readings["MACD"].status == expected_status


@pytest.mark.parametrize(("adx", "expected_status"), [(30.0, "TRENDING"), (10.0, "RANGING"), (22.0, "TRANSITIONAL")])
def test_adx_reading_status(adx, expected_status):
    snapshot = _snapshot(adx_14=adx)
    closes = np.array([100.0])
    volumes = np.array([10.0])
    readings = _by_name(explain_indicators(snapshot, closes, volumes))

    assert readings["ADX (14)"].status == expected_status


@pytest.mark.parametrize(
    ("atr", "price", "expected_status"), [(5.0, 100.0, "HIGH"), (0.5, 100.0, "LOW"), (2.0, 100.0, "MODERATE")]
)
def test_atr_reading_status_from_percent_of_price(atr, price, expected_status):
    snapshot = _snapshot(atr_14=atr)
    closes = np.array([price])
    volumes = np.array([10.0])
    readings = _by_name(explain_indicators(snapshot, closes, volumes))

    assert readings["ATR (14)"].status == expected_status


def test_obv_reading_rising_is_bullish():
    snapshot = _snapshot(obv=500.0)
    closes = np.array([100.0 + i for i in range(15)])
    volumes = np.array([10.0 + i for i in range(15)])  # rising volume with rising price -> OBV rises
    reading = _by_name(explain_indicators(snapshot, closes, volumes))["OBV"]

    assert reading.status == "BULLISH"


def test_obv_reading_not_enough_history_is_neutral():
    snapshot = _snapshot(obv=500.0)
    closes = np.array([100.0, 101.0])
    volumes = np.array([10.0, 11.0])
    reading = _by_name(explain_indicators(snapshot, closes, volumes))["OBV"]

    assert reading.status == "NEUTRAL"
    assert "enough" in reading.explanation.lower()


@pytest.mark.parametrize(
    ("k", "d", "expected_status"),
    [(85.0, 70.0, "OVERBOUGHT"), (10.0, 15.0, "OVERSOLD"), (50.0, 40.0, "BULLISH"), (40.0, 50.0, "BEARISH")],
)
def test_stoch_rsi_reading_status(k, d, expected_status):
    snapshot = _snapshot(stoch_rsi=StochRsiValues(k=k, d=d))
    closes = np.array([100.0])
    volumes = np.array([10.0])
    readings = _by_name(explain_indicators(snapshot, closes, volumes))

    assert readings["Stochastic RSI"].status == expected_status


def test_explain_indicators_returns_thirteen_readings():
    closes = np.array([100.0])
    volumes = np.array([10.0])
    readings = explain_indicators(_snapshot(), closes, volumes)

    assert len(readings) == 13
    assert len({r.name for r in readings}) == 13
