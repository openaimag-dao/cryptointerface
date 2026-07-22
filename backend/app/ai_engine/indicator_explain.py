"""Turns a raw `IndicatorSnapshot` (see `app/services/indicators/engine.py`)
into the Asset Intelligence Dashboard's Technical tab shape: every
indicator gets a `value` (display-formatted), a `status` (a short
categorical read — BULLISH/OVERSOLD/TRENDING/...), and a plain-English
`explanation`. Pure function, no I/O — same "scoring modules never do
their own I/O" discipline as `app/ai_engine/scoring/`, even though this
isn't itself a scoring module (it never feeds `market_score.py`; it's
read-only presentation of numbers the engine already computes).
"""

from dataclasses import dataclass

import numpy as np

from app.schemas.indicator import IndicatorSnapshot
from app.services.indicators.obv import obv

RSI_OVERBOUGHT = 70.0
RSI_OVERSOLD = 30.0
ADX_TRENDING = 25.0
ADX_RANGING = 20.0
ATR_HIGH_VOL_PCT = 3.0
ATR_LOW_VOL_PCT = 1.0
OBV_TREND_LOOKBACK = 10


@dataclass(frozen=True)
class IndicatorReading:
    name: str
    value: str
    status: str
    explanation: str


def _ema_reading(name: str, ema_value: float | None, price: float) -> IndicatorReading:
    if ema_value is None:
        return IndicatorReading(name, "—", "NEUTRAL", "Not enough candle history yet.")
    status = "BULLISH" if price > ema_value else "BEARISH"
    verb = "above" if price > ema_value else "below"
    return IndicatorReading(
        name, f"{ema_value:.6g}", status, f"Price is trading {verb} the {name} — {status.lower()} bias."
    )


def _ema_alignment_reading(
    ema20: float | None, ema50: float | None, ema100: float | None, ema200: float | None
) -> IndicatorReading:
    values = [ema20, ema50, ema100, ema200]
    if any(v is None for v in values):
        return IndicatorReading("EMA Alignment", "—", "NEUTRAL", "Not enough candle history for all four EMAs yet.")
    if ema20 > ema50 > ema100 > ema200:  # type: ignore[operator]
        return IndicatorReading(
            "EMA Alignment", "20 > 50 > 100 > 200", "BULLISH", "Full bullish stack — shorter EMAs above longer ones."
        )
    if ema20 < ema50 < ema100 < ema200:  # type: ignore[operator]
        return IndicatorReading(
            "EMA Alignment", "20 < 50 < 100 < 200", "BEARISH", "Full bearish stack — shorter EMAs below longer ones."
        )
    return IndicatorReading("EMA Alignment", "Mixed", "NEUTRAL", "EMAs are not cleanly stacked — no dominant trend.")


def _rsi_reading(rsi_value: float | None) -> IndicatorReading:
    if rsi_value is None:
        return IndicatorReading("RSI (14)", "—", "NEUTRAL", "Not enough candle history yet.")
    if rsi_value >= RSI_OVERBOUGHT:
        return IndicatorReading(
            "RSI (14)",
            f"{rsi_value:.1f}",
            "OVERBOUGHT",
            f"RSI at {rsi_value:.1f}, above 70 — momentum may be stretched.",
        )
    if rsi_value <= RSI_OVERSOLD:
        return IndicatorReading(
            "RSI (14)",
            f"{rsi_value:.1f}",
            "OVERSOLD",
            f"RSI at {rsi_value:.1f}, below 30 — momentum may be exhausted to the downside.",
        )
    status = "BULLISH" if rsi_value > 50 else "BEARISH"
    return IndicatorReading(
        "RSI (14)", f"{rsi_value:.1f}", status, f"RSI at {rsi_value:.1f}, on the {status.lower()} side of neutral (50)."
    )


def _macd_reading(macd_line: float | None, signal: float | None, histogram: float | None) -> IndicatorReading:
    if macd_line is None or signal is None or histogram is None:
        return IndicatorReading("MACD", "—", "NEUTRAL", "Not enough candle history yet.")
    status = "BULLISH" if histogram > 0 else "BEARISH" if histogram < 0 else "NEUTRAL"
    cross = "above" if macd_line > signal else "below"
    return IndicatorReading(
        "MACD",
        f"{macd_line:.6g} / {signal:.6g} / {histogram:.6g}",
        status,
        f"MACD line is {cross} its signal line (histogram {histogram:.6g}).",
    )


def _adx_reading(adx_value: float | None) -> IndicatorReading:
    if adx_value is None:
        return IndicatorReading("ADX (14)", "—", "NEUTRAL", "Not enough candle history yet.")
    if adx_value >= ADX_TRENDING:
        return IndicatorReading(
            "ADX (14)",
            f"{adx_value:.1f}",
            "TRENDING",
            f"ADX at {adx_value:.1f} — a real trend is in force (direction not implied).",
        )
    if adx_value <= ADX_RANGING:
        return IndicatorReading(
            "ADX (14)", f"{adx_value:.1f}", "RANGING", f"ADX at {adx_value:.1f} — price is likely chopping sideways."
        )
    return IndicatorReading(
        "ADX (14)",
        f"{adx_value:.1f}",
        "TRANSITIONAL",
        f"ADX at {adx_value:.1f} — trend strength is building but not confirmed.",
    )


def _atr_reading(atr_value: float | None, price: float) -> IndicatorReading:
    if atr_value is None or price <= 0:
        return IndicatorReading("ATR (14)", "—", "NEUTRAL", "Not enough candle history yet.")
    pct = atr_value / price * 100.0
    if pct >= ATR_HIGH_VOL_PCT:
        status = "HIGH"
    elif pct <= ATR_LOW_VOL_PCT:
        status = "LOW"
    else:
        status = "MODERATE"
    return IndicatorReading(
        "ATR (14)",
        f"{atr_value:.6g} ({pct:.2f}% of price)",
        status,
        f"{status.title()} volatility — average bar range is {pct:.2f}% of price.",
    )


def _vwap_reading(vwap_value: float | None, price: float) -> IndicatorReading:
    if vwap_value is None:
        return IndicatorReading("VWAP", "—", "NEUTRAL", "Not enough candle history yet.")
    status = "BULLISH" if price > vwap_value else "BEARISH"
    verb = "above" if price > vwap_value else "below"
    return IndicatorReading(
        "VWAP",
        f"{vwap_value:.6g}",
        status,
        f"Price is {verb} VWAP — {'buyers' if status == 'BULLISH' else 'sellers'} in control since the anchor.",
    )


def _obv_reading(obv_value: float | None, closes: np.ndarray, volumes: np.ndarray) -> IndicatorReading:
    if obv_value is None or len(closes) < OBV_TREND_LOOKBACK + 1:
        return IndicatorReading(
            "OBV",
            "—" if obv_value is None else f"{obv_value:,.0f}",
            "NEUTRAL",
            "Not enough history yet to read a trend.",
        )
    obv_series = obv(closes, volumes)
    recent = obv_series[-OBV_TREND_LOOKBACK:]
    if np.isnan(recent).any():
        return IndicatorReading("OBV", f"{obv_value:,.0f}", "NEUTRAL", "Not enough history yet to read a trend.")
    status = "BULLISH" if recent[-1] > recent[0] else "BEARISH" if recent[-1] < recent[0] else "NEUTRAL"
    direction = "rising" if status == "BULLISH" else "falling" if status == "BEARISH" else "flat"
    flow = "accumulation" if status == "BULLISH" else "distribution" if status == "BEARISH" else "no clear flow"
    return IndicatorReading(
        "OBV",
        f"{obv_value:,.0f}",
        status,
        f"On-Balance Volume is {direction} over the last {OBV_TREND_LOOKBACK} bars — {flow}.",
    )


def _stoch_rsi_reading(k: float | None, d: float | None) -> IndicatorReading:
    if k is None or d is None:
        return IndicatorReading("Stochastic RSI", "—", "NEUTRAL", "Not enough candle history yet.")
    if k >= 80:
        status = "OVERBOUGHT"
    elif k <= 20:
        status = "OVERSOLD"
    else:
        status = "BULLISH" if k > d else "BEARISH"
    return IndicatorReading("Stochastic RSI", f"K {k:.1f} / D {d:.1f}", status, f"%K at {k:.1f}, %D at {d:.1f}.")


def _pivot_reading(pivot: float | None, price: float) -> IndicatorReading:
    if pivot is None:
        return IndicatorReading("Pivot Point", "—", "NEUTRAL", "Not enough candle history yet.")
    status = "BULLISH" if price > pivot else "BEARISH"
    verb = "above" if price > pivot else "below"
    return IndicatorReading(
        "Pivot Point", f"{pivot:.6g}", status, f"Price is trading {verb} the floor-trader pivot ({pivot:.6g})."
    )


def explain_indicators(snapshot: IndicatorSnapshot, closes: np.ndarray, volumes: np.ndarray) -> list[IndicatorReading]:
    price = float(closes[-1]) if len(closes) else 0.0

    return [
        _ema_reading("EMA20", snapshot.ema.ema_20, price),
        _ema_reading("EMA50", snapshot.ema.ema_50, price),
        _ema_reading("EMA100", snapshot.ema.ema_100, price),
        _ema_reading("EMA200", snapshot.ema.ema_200, price),
        _ema_alignment_reading(snapshot.ema.ema_20, snapshot.ema.ema_50, snapshot.ema.ema_100, snapshot.ema.ema_200),
        _rsi_reading(snapshot.rsi_14),
        _macd_reading(snapshot.macd.macd, snapshot.macd.signal, snapshot.macd.histogram),
        _adx_reading(snapshot.adx_14),
        _atr_reading(snapshot.atr_14, price),
        _vwap_reading(snapshot.vwap, price),
        _obv_reading(snapshot.obv, closes, volumes),
        _stoch_rsi_reading(snapshot.stoch_rsi.k, snapshot.stoch_rsi.d),
        _pivot_reading(snapshot.pivot.pivot, price),
    ]
