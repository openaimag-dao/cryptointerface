from dataclasses import dataclass

import numpy as np
import pytest

from app.services.indicators.adx import adx
from app.services.indicators.atr import atr
from app.services.indicators.bollinger import bollinger_bands
from app.services.indicators.ema import ema
from app.services.indicators.engine import compute_indicators
from app.services.indicators.macd import macd
from app.services.indicators.obv import obv
from app.services.indicators.rsi import rsi
from app.services.indicators.stoch_rsi import stoch_rsi
from app.services.indicators.vwap import vwap


@dataclass
class Candle:
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float


def make_candles(closes: list[float], volume: float = 1000.0) -> list[Candle]:
    candles = []
    for i, close in enumerate(closes):
        prev = closes[i - 1] if i > 0 else close
        candles.append(
            Candle(
                time=1_700_000_000 + i * 3600,
                open=prev,
                high=max(prev, close) + 0.5,
                low=min(prev, close) - 0.5,
                close=close,
                volume=volume,
            )
        )
    return candles


class TestEma:
    def test_warmup_is_nan(self):
        values = np.arange(1, 11, dtype=float)
        result = ema(values, period=20)
        assert np.all(np.isnan(result))

    def test_known_value(self):
        # Classic textbook EMA example: prices 22.27..22.29 style sequences
        # are overkill here — assert against a hand-computed simple case.
        values = np.array([1, 2, 3, 4, 5], dtype=float)
        result = ema(values, period=3)
        assert np.isnan(result[0])
        assert np.isnan(result[1])
        assert result[2] == pytest.approx(2.0)  # seed = mean(1,2,3)
        alpha = 2 / 4
        expected_3 = 4 * alpha + 2.0 * (1 - alpha)
        assert result[3] == pytest.approx(expected_3)


class TestRsi:
    def test_all_gains_is_100(self):
        values = np.arange(1, 30, dtype=float)  # strictly increasing
        result = rsi(values, period=14)
        assert result[-1] == pytest.approx(100.0)

    def test_all_losses_is_0(self):
        values = np.arange(30, 1, -1, dtype=float)  # strictly decreasing
        result = rsi(values, period=14)
        assert result[-1] == pytest.approx(0.0)

    def test_bounded_0_100(self):
        rng = np.random.default_rng(1)
        values = 100 + np.cumsum(rng.normal(0, 1, 100))
        result = rsi(values, period=14)
        valid = result[~np.isnan(result)]
        assert np.all(valid >= 0) and np.all(valid <= 100)


class TestMacd:
    def test_shapes_match_input(self):
        values = np.linspace(100, 150, 60)
        macd_line, signal_line, histogram = macd(values)
        assert len(macd_line) == len(values) == len(signal_line) == len(histogram)

    def test_histogram_is_macd_minus_signal(self):
        values = np.linspace(100, 150, 60)
        macd_line, signal_line, histogram = macd(values)
        valid = ~np.isnan(histogram)
        np.testing.assert_allclose(histogram[valid], (macd_line - signal_line)[valid])


class TestAtr:
    def test_zero_range_gives_zero_atr(self):
        high = np.full(20, 100.0)
        low = np.full(20, 100.0)
        close = np.full(20, 100.0)
        result = atr(high, low, close, period=14)
        assert result[-1] == pytest.approx(0.0)


class TestBollinger:
    def test_flat_series_zero_width(self):
        close = np.full(25, 50.0)
        upper, middle, lower = bollinger_bands(close, period=20)
        assert upper[-1] == pytest.approx(middle[-1])
        assert lower[-1] == pytest.approx(middle[-1])

    def test_upper_above_lower(self):
        rng = np.random.default_rng(2)
        close = 100 + np.cumsum(rng.normal(0, 1, 40))
        upper, middle, lower = bollinger_bands(close, period=20)
        assert upper[-1] > middle[-1] > lower[-1]


class TestVwap:
    def test_constant_price_equals_price(self):
        high = np.full(10, 100.0)
        low = np.full(10, 100.0)
        close = np.full(10, 100.0)
        volume = np.full(10, 50.0)
        result = vwap(high, low, close, volume)
        assert result[-1] == pytest.approx(100.0)


class TestObv:
    def test_monotonic_up_accumulates_volume(self):
        close = np.array([1, 2, 3, 4], dtype=float)
        volume = np.array([10, 10, 10, 10], dtype=float)
        result = obv(close, volume)
        assert result[-1] == pytest.approx(40.0)

    def test_monotonic_down_subtracts_volume(self):
        close = np.array([4, 3, 2, 1], dtype=float)
        volume = np.array([10, 10, 10, 10], dtype=float)
        result = obv(close, volume)
        assert result[-1] == pytest.approx(-20.0)


class TestAdx:
    def test_strong_trend_produces_high_adx(self):
        n = 60
        close = np.linspace(100, 200, n)
        high = close + 1
        low = close - 1
        result = adx(high, low, close, period=14)
        assert result[-1] > 30  # strong sustained trend


class TestStochRsi:
    def test_bounded_0_100(self):
        rng = np.random.default_rng(3)
        close = 100 + np.cumsum(rng.normal(0, 1, 80))
        k, d = stoch_rsi(close)
        valid_k = k[~np.isnan(k)]
        valid_d = d[~np.isnan(d)]
        assert np.all(valid_k >= -1e-9) and np.all(valid_k <= 100 + 1e-9)
        assert np.all(valid_d >= -1e-9) and np.all(valid_d <= 100 + 1e-9)


class TestEngine:
    def test_snapshot_has_all_fields_after_warmup(self):
        rng = np.random.default_rng(4)
        closes = list(100 + np.cumsum(rng.normal(0, 1, 250)))
        candles = make_candles(closes)

        snapshot = compute_indicators("BTCUSDT", "1h", candles)

        assert snapshot.symbol == "BTCUSDT"
        assert snapshot.interval == "1h"
        assert snapshot.time == candles[-1].time
        assert snapshot.ema.ema_200 is not None
        assert snapshot.rsi_14 is not None
        assert snapshot.macd.histogram is not None
        assert snapshot.atr_14 is not None
        assert snapshot.bollinger_bands.upper is not None
        assert snapshot.vwap is not None
        assert snapshot.adx_14 is not None
        assert snapshot.obv is not None
        assert snapshot.stoch_rsi.k is not None
        assert snapshot.pivot.pivot is not None

    def test_raises_on_empty_series(self):
        with pytest.raises(ValueError):
            compute_indicators("BTCUSDT", "1h", [])
