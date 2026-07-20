"""Indicator orchestrator.

Takes a chronologically-ordered candle series and computes every indicator
in one pass, returning a single typed snapshot for the latest candle. Runs
automatically whenever a new candle closes (see `app.tasks.live_feed`).

To add a new indicator: write a pure `numpy`-in/`numpy`-out function in this
package (see `ema.py` for the simplest example), call it below, and add the
matching field to `app.schemas.indicator.IndicatorSnapshot`.
"""

from typing import Protocol

import numpy as np

from app.schemas.indicator import (
    BollingerBandsValues,
    EmaValues,
    IndicatorSnapshot,
    MacdValues,
    PivotLevels,
    StochRsiValues,
)
from app.services.indicators.adx import adx
from app.services.indicators.atr import atr
from app.services.indicators.bollinger import bollinger_bands
from app.services.indicators.ema import ema
from app.services.indicators.macd import macd
from app.services.indicators.obv import obv
from app.services.indicators.pivot import pivot_points
from app.services.indicators.rsi import rsi
from app.services.indicators.stoch_rsi import stoch_rsi
from app.services.indicators.vwap import vwap


class CandleLike(Protocol):
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float


def _last_or_none(values: np.ndarray) -> float | None:
    if len(values) == 0:
        return None
    value = values[-1]
    return None if np.isnan(value) else float(value)


def compute_indicators(symbol: str, interval: str, candles: list[CandleLike]) -> IndicatorSnapshot:
    if not candles:
        raise ValueError("Cannot compute indicators from an empty candle series")

    highs = np.array([c.high for c in candles], dtype=float)
    lows = np.array([c.low for c in candles], dtype=float)
    closes = np.array([c.close for c in candles], dtype=float)
    volumes = np.array([c.volume for c in candles], dtype=float)

    macd_line, signal_line, histogram = macd(closes)
    bb_upper, bb_middle, bb_lower = bollinger_bands(closes)
    stoch_k, stoch_d = stoch_rsi(closes)
    pivots = pivot_points(highs, lows, closes)

    return IndicatorSnapshot(
        symbol=symbol,
        interval=interval,
        time=candles[-1].time,
        ema=EmaValues(
            ema_20=_last_or_none(ema(closes, 20)),
            ema_50=_last_or_none(ema(closes, 50)),
            ema_100=_last_or_none(ema(closes, 100)),
            ema_200=_last_or_none(ema(closes, 200)),
        ),
        rsi_14=_last_or_none(rsi(closes, 14)),
        macd=MacdValues(
            macd=_last_or_none(macd_line),
            signal=_last_or_none(signal_line),
            histogram=_last_or_none(histogram),
        ),
        atr_14=_last_or_none(atr(highs, lows, closes, 14)),
        bollinger_bands=BollingerBandsValues(
            upper=_last_or_none(bb_upper),
            middle=_last_or_none(bb_middle),
            lower=_last_or_none(bb_lower),
        ),
        vwap=_last_or_none(vwap(highs, lows, closes, volumes)),
        adx_14=_last_or_none(adx(highs, lows, closes, 14)),
        obv=_last_or_none(obv(closes, volumes)),
        stoch_rsi=StochRsiValues(k=_last_or_none(stoch_k), d=_last_or_none(stoch_d)),
        pivot=PivotLevels(
            pivot=_last_or_none(pivots["pivot"]),
            r1=_last_or_none(pivots["r1"]),
            r2=_last_or_none(pivots["r2"]),
            r3=_last_or_none(pivots["r3"]),
            s1=_last_or_none(pivots["s1"]),
            s2=_last_or_none(pivots["s2"]),
            s3=_last_or_none(pivots["s3"]),
        ),
    )
