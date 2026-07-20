"""Structure Engine.

Reads classic floor-trader pivot levels and swing-point support/resistance
to detect where price sits relative to the local market structure, and
whether it has broken out above resistance or broken down below support.

Score composition (starts at neutral 50):
  +/-10  price vs the rolling pivot point
  +/-20  price breaking above the nearest swing-high resistance / below the
         nearest swing-low support (breakout / breakdown)
"""

import numpy as np

from app.ai_engine.types import FactorScore, find_swing_indices, last_valid, make_factor_score
from app.services.indicators.pivot import pivot_points

SWING_WINDOW = 3
BREAKOUT_POINTS = 20.0
PIVOT_POINTS = 10.0


def score_structure(closes: np.ndarray, highs: np.ndarray, lows: np.ndarray) -> FactorScore:
    reasons: list[str] = []
    details: dict[str, float | str | bool | int] = {}
    bullish = 0.0
    bearish = 0.0
    price = float(closes[-1])

    levels = pivot_points(highs, lows, closes)
    pivot_last = last_valid(levels["pivot"])
    if pivot_last is not None:
        details["pivot"] = round(pivot_last, 6)
        for key in ("r1", "r2", "s1", "s2"):
            value = last_valid(levels[key])
            details[key] = round(value, 6) if value is not None else "unavailable"

        if price > pivot_last:
            bullish += PIVOT_POINTS
            reasons.append(f"Price ({price:.6g}) trading above the pivot point ({pivot_last:.6g})")
        else:
            bearish += PIVOT_POINTS
            reasons.append(f"Price ({price:.6g}) trading below the pivot point ({pivot_last:.6g})")
    else:
        reasons.append("Not enough history yet for pivot levels")

    swing_high_idx = find_swing_indices(highs, SWING_WINDOW, find_highs=True)
    swing_low_idx = find_swing_indices(lows, SWING_WINDOW, find_highs=False)

    if swing_high_idx:
        resistance = float(highs[swing_high_idx[-1]])
        details["nearest_resistance"] = round(resistance, 6)
        if price > resistance:
            bullish += BREAKOUT_POINTS
            reasons.append(f"Price broke above prior swing-high resistance at {resistance:.6g} (breakout)")
        else:
            distance_pct = (resistance - price) / price * 100 if price else 0.0
            reasons.append(f"Nearest resistance at {resistance:.6g} ({distance_pct:.2f}% above price)")
    else:
        reasons.append("Not enough history yet to identify swing-high resistance")

    if swing_low_idx:
        support = float(lows[swing_low_idx[-1]])
        details["nearest_support"] = round(support, 6)
        if price < support:
            bearish += BREAKOUT_POINTS
            reasons.append(f"Price broke below prior swing-low support at {support:.6g} (breakdown)")
        else:
            distance_pct = (price - support) / price * 100 if price else 0.0
            reasons.append(f"Nearest support at {support:.6g} ({distance_pct:.2f}% below price)")
    else:
        reasons.append("Not enough history yet to identify swing-low support")

    score = 50.0 + bullish - bearish
    if not reasons:
        reasons.append("Insufficient candle history for a structure read")

    factor = make_factor_score("structure", score, reasons, details)
    factor.details["structure_score"] = factor.score
    factor.details["structure_direction"] = factor.direction
    factor.details["structure_strength"] = factor.strength
    return factor
