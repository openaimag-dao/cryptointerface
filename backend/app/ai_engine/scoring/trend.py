"""Trend Engine.

Reads EMA20/50/100/200 alignment, EMA50 slope, and Higher-High/Higher-Low
(or Lower-High/Lower-Low) swing structure into a single trend score.

Score composition (starts at neutral 50):
  +/-10  each for EMA20 vs EMA50, EMA50 vs EMA100, EMA100 vs EMA200 (3 pairs = up to 30)
  +/-10  price vs EMA200 (long-term trend filter)
  +/-15  EMA50 slope magnitude over the last 10 bars (scaled, capped)
  +/-15  confirmed HH+HL / LH+LL swing structure
Max/min score is therefore clamped to [0, 100] by `make_factor_score`.
"""

import numpy as np

from app.ai_engine.types import FactorScore, clamp, find_swing_indices, last_valid, make_factor_score
from app.services.indicators.ema import ema

EMA_PERIODS = (20, 50, 100, 200)
SLOPE_LOOKBACK_BARS = 10
SLOPE_SCALE = 20.0  # 0.75% EMA50 move over the lookback window -> full slope points
SWING_WINDOW = 3  # bars required on each side to confirm a local swing high/low


def score_trend(closes: np.ndarray, highs: np.ndarray, lows: np.ndarray) -> FactorScore:
    reasons: list[str] = []
    details: dict[str, float | str | bool | int] = {}
    bullish = 0.0
    bearish = 0.0

    ema_values: dict[int, float | None] = {period: last_valid(ema(closes, period)) for period in EMA_PERIODS}
    for period, value in ema_values.items():
        details[f"ema{period}"] = value if value is not None else "unavailable"

    if all(v is not None for v in ema_values.values()):
        e20, e50, e100, e200 = (ema_values[p] for p in EMA_PERIODS)  # type: ignore[misc]

        for label_a, val_a, label_b, val_b in (
            ("EMA20", e20, "EMA50", e50),
            ("EMA50", e50, "EMA100", e100),
            ("EMA100", e100, "EMA200", e200),
        ):
            if val_a > val_b:
                bullish += 10.0
                reasons.append(f"{label_a} above {label_b}")
            else:
                bearish += 10.0
                reasons.append(f"{label_a} below {label_b}")

        if closes[-1] > e200:
            bullish += 10.0
            reasons.append("Price trading above EMA200")
        else:
            bearish += 10.0
            reasons.append("Price trading below EMA200")
    else:
        reasons.append("Not enough history yet for full EMA20/50/100/200 alignment")

    ema50_series = ema(closes, 50)
    valid_idx = np.where(~np.isnan(ema50_series))[0]
    slope_pct: float | None = None
    if len(valid_idx) > SLOPE_LOOKBACK_BARS:
        end_idx = valid_idx[-1]
        start_value = ema50_series[end_idx - SLOPE_LOOKBACK_BARS]
        end_value = ema50_series[end_idx]
        if start_value != 0:
            slope_pct = (end_value - start_value) / abs(start_value) * 100
    details["ema50_slope_pct"] = round(slope_pct, 4) if slope_pct is not None else "unavailable"

    if slope_pct is not None:
        slope_points = clamp(abs(slope_pct) * SLOPE_SCALE, 0, 15)
        if slope_pct > 0:
            bullish += slope_points
            if slope_points >= 3:
                reasons.append(f"EMA50 sloping upward ({slope_pct:.2f}% over {SLOPE_LOOKBACK_BARS} bars)")
        elif slope_pct < 0:
            bearish += slope_points
            if slope_points >= 3:
                reasons.append(f"EMA50 sloping downward ({slope_pct:.2f}% over {SLOPE_LOOKBACK_BARS} bars)")

    swing_high_idx = find_swing_indices(highs, SWING_WINDOW, find_highs=True)
    swing_low_idx = find_swing_indices(lows, SWING_WINDOW, find_highs=False)

    higher_high = len(swing_high_idx) >= 2 and highs[swing_high_idx[-1]] > highs[swing_high_idx[-2]]
    higher_low = len(swing_low_idx) >= 2 and lows[swing_low_idx[-1]] > lows[swing_low_idx[-2]]
    lower_high = len(swing_high_idx) >= 2 and highs[swing_high_idx[-1]] < highs[swing_high_idx[-2]]
    lower_low = len(swing_low_idx) >= 2 and lows[swing_low_idx[-1]] < lows[swing_low_idx[-2]]

    details["higher_high"] = bool(higher_high)
    details["higher_low"] = bool(higher_low)
    details["lower_high"] = bool(lower_high)
    details["lower_low"] = bool(lower_low)

    if higher_high and higher_low:
        bullish += 15.0
        reasons.append("Higher highs and higher lows confirmed (bullish structure)")
    elif lower_high and lower_low:
        bearish += 15.0
        reasons.append("Lower highs and lower lows confirmed (bearish structure)")

    score = 50.0 + bullish - bearish
    if not reasons:
        reasons.append("Insufficient candle history for a trend read")

    factor = make_factor_score("trend", score, reasons, details)
    # Expose the spec's named fields explicitly (trend_score/trend_direction/trend_strength)
    # as details too, so API consumers don't have to know the generic FactorScore shape.
    factor.details["trend_score"] = factor.score
    factor.details["trend_direction"] = factor.direction
    factor.details["trend_strength"] = factor.strength
    return factor
