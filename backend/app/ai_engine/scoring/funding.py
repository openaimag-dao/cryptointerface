"""Funding Engine.

Reads the latest perpetual futures funding rate and its recent trend.
Funding sentiment is contrarian at the extremes: a heavily positive rate
means longs are paying shorts to stay open (the crowd is over-long, which
is a classic squeeze setup), so it's scored bearish; a heavily negative
rate means the crowd is over-short, scored bullish. Mild funding within
the extreme band is scored the way the crowd is actually leaning (a small
positive rate is a small bullish tilt, not a contrarian signal).

Score composition (starts at neutral 50):
  +/-25  extreme funding rate (contrarian: extreme positive -> bearish,
         extreme negative -> bullish)
  +/-10  mild funding rate (follows the crowd's lean, sub-extreme band)
Funding trend across recent readings is surfaced as a reason only (no
extra points) since it's a secondary confirmation, not a primary signal.
"""

from app.ai_engine.types import FactorScore, clamp, make_factor_score
from app.models.funding import FundingRate

NEUTRAL_BAND = 0.0001  # 0.01% per funding interval - within this, treat as balanced
EXTREME_THRESHOLD = 0.0005  # 0.05% per funding interval - crowd is heavily one-sided
MILD_SCALE = 60_000.0  # 0.01% -> 6 points, capped at 10
EXTREME_SCALE = 30_000.0  # scales the extra distance past the extreme threshold
TREND_LOOKBACK = 5
TREND_EPSILON = 0.0001


def score_funding(funding_history: list[FundingRate]) -> FactorScore:
    reasons: list[str] = []
    details: dict[str, float | str | bool | int] = {}
    bullish = 0.0
    bearish = 0.0

    if not funding_history:
        reasons.append("No funding rate data available yet")
        factor = make_factor_score("funding", 50.0, reasons, details)
        factor.details["funding_score"] = factor.score
        factor.details["funding_direction"] = factor.direction
        factor.details["funding_strength"] = factor.strength
        return factor

    rate = funding_history[-1].funding_rate
    details["funding_rate"] = round(rate, 6)
    abs_rate = abs(rate)

    if abs_rate >= EXTREME_THRESHOLD:
        points = clamp(10.0 + (abs_rate - EXTREME_THRESHOLD) * EXTREME_SCALE, 10, 25)
        if rate > 0:
            bearish += points
            reasons.append(
                f"Funding rate extremely positive ({rate * 100:.4f}%) — longs crowded, contrarian bearish signal"
            )
        else:
            bullish += points
            reasons.append(
                f"Funding rate extremely negative ({rate * 100:.4f}%) — shorts crowded, contrarian bullish signal"
            )
    elif abs_rate >= NEUTRAL_BAND:
        points = clamp(abs_rate * MILD_SCALE, 0, 10)
        if rate > 0:
            bullish += points
            reasons.append(f"Funding rate mildly positive ({rate * 100:.4f}%), majority positioned long")
        else:
            bearish += points
            reasons.append(f"Funding rate mildly negative ({rate * 100:.4f}%), majority positioned short")
    else:
        reasons.append(f"Funding rate near zero ({rate * 100:.4f}%), balanced long/short positioning")

    if len(funding_history) >= 3:
        window = funding_history[-min(len(funding_history), TREND_LOOKBACK) :]
        trend = window[-1].funding_rate - window[0].funding_rate
        details["funding_trend"] = round(trend, 6)
        if trend > TREND_EPSILON:
            reasons.append("Funding rate trending upward over recent periods (growing long bias)")
        elif trend < -TREND_EPSILON:
            reasons.append("Funding rate trending downward over recent periods (growing short bias)")

    score = 50.0 + bullish - bearish
    factor = make_factor_score("funding", score, reasons, details)
    factor.details["funding_score"] = factor.score
    factor.details["funding_direction"] = factor.direction
    factor.details["funding_strength"] = factor.strength
    return factor
