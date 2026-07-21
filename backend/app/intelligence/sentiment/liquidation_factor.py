"""Scores recent liquidation activity as a contrarian sentiment signal.

Heavy long liquidations (over-leveraged longs forced out) often mark local
capitulation bottoms — scored mildly bullish, the same "contrarian at the
extremes" read `app/ai_engine/scoring/funding.py` already uses for
one-sided funding. Heavy short liquidations (a short squeeze) often mark
local tops — scored mildly bearish.

This is a Sentiment Engine input only (`engine.py`) — it is not wired
into `app/ai_engine/market_score.py`'s `FACTOR_WEIGHTS`, so it has no
effect on the Decision Engine's Market Score/Direction.
"""

from app.ai_engine.types import FactorScore, clamp, make_factor_score

MIN_MEANINGFUL_TOTAL_USD = 500_000.0  # below this, 24h liquidations are too thin to read
MAX_POINTS = 20.0
IMBALANCE_SCALE = 40.0


def score_liquidations(totals: dict[str, float]) -> FactorScore:
    long_usd = totals.get("LONG", 0.0)
    short_usd = totals.get("SHORT", 0.0)
    total = long_usd + short_usd

    reasons: list[str] = []
    details: dict[str, float | str | bool | int] = {"long_usd_24h": long_usd, "short_usd_24h": short_usd}

    if total < MIN_MEANINGFUL_TOTAL_USD:
        reasons.append(f"Trailing 24h liquidations too thin (${total:,.0f}) to read as a sentiment signal")
        score = 50.0
    else:
        imbalance = (long_usd - short_usd) / total  # +1 all-long .. -1 all-short
        points = clamp(abs(imbalance) * IMBALANCE_SCALE, 0, MAX_POINTS)
        if long_usd > short_usd:
            score = 50.0 + points
            reasons.append(
                f"Long liquidations (${long_usd:,.0f}) dominate over shorts (${short_usd:,.0f}) in the trailing "
                "24h — often a capitulation/washout, contrarian bullish"
            )
        else:
            score = 50.0 - points
            reasons.append(
                f"Short liquidations (${short_usd:,.0f}) dominate over longs (${long_usd:,.0f}) in the trailing "
                "24h — often a short squeeze exhausting, contrarian bearish"
            )

    factor = make_factor_score("liquidations", score, reasons, details)
    factor.details["liquidations_score"] = factor.score
    factor.details["liquidations_direction"] = factor.direction
    factor.details["liquidations_strength"] = factor.strength
    return factor
