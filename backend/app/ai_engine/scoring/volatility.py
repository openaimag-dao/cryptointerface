"""Volatility Engine.

Reads ATR trend and Bollinger Band width to detect range expansion vs
compression, then aligns any detected expansion with the concurrent price
direction to produce a directional score (volatility itself is symmetric —
it's only bullish or bearish once paired with which way price is moving
while it expands).

Score composition (starts at neutral 50):
  +/-20  ATR expanding, aligned with the recent price return
  +/-20  Bollinger Band width expanding beyond its recent average, aligned
         with the recent price return
  +/-10  Price pressing the upper/lower Bollinger Band
A detected squeeze (compression) contributes no directional points but is
surfaced as a reason — it signals a breakout may be imminent without
implying a direction yet.
"""

import numpy as np

from app.ai_engine.types import FactorScore, clamp, last_valid_index, make_factor_score
from app.services.indicators.atr import atr
from app.services.indicators.bollinger import bollinger_bands

ATR_LOOKBACK_BARS = 14
ATR_EXPANSION_THRESHOLD_PCT = 10.0
RETURN_LOOKBACK_BARS = 5
BB_AVG_WINDOW = 20
BB_SQUEEZE_RATIO = 0.8
BB_EXPANSION_RATIO = 1.2


def score_volatility(closes: np.ndarray, highs: np.ndarray, lows: np.ndarray) -> FactorScore:
    reasons: list[str] = []
    details: dict[str, float | str | bool | int] = {}
    bullish = 0.0
    bearish = 0.0

    recent_return_pct: float | None = None
    if len(closes) > RETURN_LOOKBACK_BARS and closes[-1 - RETURN_LOOKBACK_BARS] != 0:
        base = closes[-1 - RETURN_LOOKBACK_BARS]
        recent_return_pct = float((closes[-1] - base) / base * 100)
    details["recent_return_pct"] = round(recent_return_pct, 3) if recent_return_pct is not None else "unavailable"

    atr_series = atr(highs, lows, closes)
    atr_end_idx = last_valid_index(atr_series)
    atr_pct_change: float | None = None
    if atr_end_idx is not None and atr_end_idx - ATR_LOOKBACK_BARS >= 0:
        atr_last = atr_series[atr_end_idx]
        atr_start = atr_series[atr_end_idx - ATR_LOOKBACK_BARS]
        details["atr"] = round(float(atr_last), 4)
        if atr_start > 0:
            atr_pct_change = float((atr_last - atr_start) / atr_start * 100)
    details["atr_pct_change"] = round(atr_pct_change, 2) if atr_pct_change is not None else "unavailable"

    if atr_pct_change is not None:
        if atr_pct_change > ATR_EXPANSION_THRESHOLD_PCT:
            points = clamp(atr_pct_change * 0.5, 0, 20)
            if recent_return_pct is not None and recent_return_pct > 0:
                bullish += points
                reasons.append(f"ATR expanding ({atr_pct_change:.1f}%) alongside rising price")
            elif recent_return_pct is not None and recent_return_pct < 0:
                bearish += points
                reasons.append(f"ATR expanding ({atr_pct_change:.1f}%) alongside falling price")
            else:
                reasons.append(f"ATR expanding ({atr_pct_change:.1f}%) but recent price direction is flat")
        elif atr_pct_change < -ATR_EXPANSION_THRESHOLD_PCT:
            reasons.append(f"ATR contracting ({atr_pct_change:.1f}%), volatility cooling off")
        else:
            reasons.append(f"ATR stable ({atr_pct_change:.1f}%), no notable range expansion or compression")
    else:
        reasons.append("Not enough history yet for an ATR trend read")

    upper, middle, lower = bollinger_bands(closes)
    with np.errstate(invalid="ignore", divide="ignore"):
        bandwidth = np.where(middle > 0, (upper - lower) / middle, np.nan)
    bw_end_idx = last_valid_index(bandwidth)

    if bw_end_idx is not None and bw_end_idx - BB_AVG_WINDOW + 1 >= 0:
        bw_last = float(bandwidth[bw_end_idx])
        bw_window = bandwidth[bw_end_idx - BB_AVG_WINDOW + 1 : bw_end_idx + 1]
        bw_avg = float(np.mean(bw_window))
        details["bb_bandwidth"] = round(bw_last, 4)
        details["bb_bandwidth_avg"] = round(bw_avg, 4)

        if bw_avg > 0:
            ratio = bw_last / bw_avg
            if ratio < BB_SQUEEZE_RATIO:
                details["bb_squeeze"] = True
                reasons.append(
                    f"Bollinger Band squeeze detected (bandwidth at {ratio * 100:.0f}% of its "
                    f"{BB_AVG_WINDOW}-bar average) — breakout likely"
                )
            else:
                details["bb_squeeze"] = False
                if ratio > BB_EXPANSION_RATIO:
                    points = clamp((ratio - 1.0) * 30, 0, 20)
                    if recent_return_pct is not None and recent_return_pct > 0:
                        bullish += points
                        reasons.append(f"Bollinger Bands expanding ({ratio:.2f}x average) with an upward price move")
                    elif recent_return_pct is not None and recent_return_pct < 0:
                        bearish += points
                        reasons.append(f"Bollinger Bands expanding ({ratio:.2f}x average) with a downward price move")
                    else:
                        reasons.append(
                            f"Bollinger Bands expanding ({ratio:.2f}x average) but recent price direction is flat"
                        )
                else:
                    reasons.append(
                        f"Bollinger Band width near its {BB_AVG_WINDOW}-bar average ({ratio:.2f}x), "
                        "no squeeze or expansion signal"
                    )
        else:
            details["bb_squeeze"] = False
            reasons.append("Bollinger Bands flat (zero width), no volatility signal available")

        upper_last = float(upper[bw_end_idx])
        lower_last = float(lower[bw_end_idx])
        if upper_last > lower_last:
            band_position = (closes[-1] - lower_last) / (upper_last - lower_last)
            details["bb_position_pct"] = round(float(band_position * 100), 1)
            if band_position >= 0.95:
                bullish += 10.0
                reasons.append("Price pressing the upper Bollinger Band")
            elif band_position <= 0.05:
                bearish += 10.0
                reasons.append("Price pressing the lower Bollinger Band")
    else:
        reasons.append("Not enough history yet for a Bollinger Band read")

    score = 50.0 + bullish - bearish
    if not reasons:
        reasons.append("Insufficient candle history for a volatility read")

    factor = make_factor_score("volatility", score, reasons, details)
    factor.details["volatility_score"] = factor.score
    factor.details["volatility_direction"] = factor.direction
    factor.details["volatility_strength"] = factor.strength
    return factor
