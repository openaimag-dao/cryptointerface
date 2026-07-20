"""Open Interest Engine.

Reads open-interest growth/decline paired with the concurrent price move
into the classic OI/price divergence matrix:

  price up   + OI up    -> new longs entering, trend confirmed (strong bullish)
  price down + OI up    -> new shorts entering, trend confirmed (strong bearish)
  price up   + OI down  -> short covering, not new conviction (weak bullish)
  price down + OI down  -> long liquidation / de-risking (weak bearish)

Score composition (starts at neutral 50):
  +/-20  strong case (OI and price move together)
  +/-10  weak case (OI and price move opposite each other — a divergence)
"""

import numpy as np

from app.ai_engine.types import FactorScore, clamp, make_factor_score
from app.models.open_interest import OpenInterest

OI_CHANGE_THRESHOLD_PCT = 2.0
PRICE_CHANGE_THRESHOLD_PCT = 0.5
PRICE_LOOKBACK_BARS = 20
STRONG_SCALE = 4.0
WEAK_SCALE = 2.0


def score_oi(closes: np.ndarray, oi_history: list[OpenInterest]) -> FactorScore:
    reasons: list[str] = []
    details: dict[str, float | str | bool | int] = {}
    bullish = 0.0
    bearish = 0.0

    if len(oi_history) < 2:
        reasons.append("Not enough open interest history yet")
        factor = make_factor_score("oi", 50.0, reasons, details)
        factor.details["oi_score"] = factor.score
        factor.details["oi_direction"] = factor.direction
        factor.details["oi_strength"] = factor.strength
        return factor

    latest_oi = oi_history[-1].open_interest
    prior_oi = oi_history[0].open_interest
    details["open_interest"] = round(latest_oi, 4)

    oi_change_pct: float | None = None
    if prior_oi > 0:
        oi_change_pct = (latest_oi - prior_oi) / prior_oi * 100
    details["oi_change_pct"] = round(oi_change_pct, 2) if oi_change_pct is not None else "unavailable"

    price_change_pct: float | None = None
    if len(closes) > PRICE_LOOKBACK_BARS and closes[-1 - PRICE_LOOKBACK_BARS] != 0:
        base = closes[-1 - PRICE_LOOKBACK_BARS]
        price_change_pct = float((closes[-1] - base) / base * 100)
    details["price_change_pct"] = round(price_change_pct, 2) if price_change_pct is not None else "unavailable"

    if oi_change_pct is None or price_change_pct is None:
        reasons.append("Not enough aligned price/open-interest history for a divergence read")
        factor = make_factor_score("oi", 50.0, reasons, details)
        factor.details["oi_score"] = factor.score
        factor.details["oi_direction"] = factor.direction
        factor.details["oi_strength"] = factor.strength
        return factor

    oi_rising = oi_change_pct > OI_CHANGE_THRESHOLD_PCT
    oi_falling = oi_change_pct < -OI_CHANGE_THRESHOLD_PCT
    price_rising = price_change_pct > PRICE_CHANGE_THRESHOLD_PCT
    price_falling = price_change_pct < -PRICE_CHANGE_THRESHOLD_PCT

    if oi_rising and price_rising:
        points = clamp(min(oi_change_pct, price_change_pct) * STRONG_SCALE, 10, 20)
        bullish += points
        reasons.append(
            f"Open interest rising ({oi_change_pct:.1f}%) alongside rising price ({price_change_pct:.1f}%) "
            "— new longs entering, trend confirmed"
        )
    elif oi_rising and price_falling:
        points = clamp(min(oi_change_pct, abs(price_change_pct)) * STRONG_SCALE, 10, 20)
        bearish += points
        reasons.append(
            f"Open interest rising ({oi_change_pct:.1f}%) while price falls ({price_change_pct:.1f}%) "
            "— new shorts entering, trend confirmed"
        )
    elif oi_falling and price_rising:
        points = clamp(min(abs(oi_change_pct), price_change_pct) * WEAK_SCALE, 5, 10)
        bullish += points
        reasons.append(
            f"Open interest falling ({oi_change_pct:.1f}%) while price rises ({price_change_pct:.1f}%) "
            "— likely short covering, not new conviction (weak bullish)"
        )
    elif oi_falling and price_falling:
        points = clamp(min(abs(oi_change_pct), abs(price_change_pct)) * WEAK_SCALE, 5, 10)
        bearish += points
        reasons.append(
            f"Open interest falling ({oi_change_pct:.1f}%) alongside falling price ({price_change_pct:.1f}%) "
            "— long liquidation / de-risking (weak bearish)"
        )
    else:
        reasons.append(
            f"Open interest change ({oi_change_pct:.1f}%) and price change ({price_change_pct:.1f}%) "
            "show no significant divergence signal"
        )

    score = 50.0 + bullish - bearish
    factor = make_factor_score("oi", score, reasons, details)
    factor.details["oi_score"] = factor.score
    factor.details["oi_direction"] = factor.direction
    factor.details["oi_strength"] = factor.strength
    return factor
