"""Confidence Engine.

A deterministic, transparent 0-100 confidence score with no randomness —
every run over the same inputs produces the exact same number. Confidence
answers a different question than the Market Score: the score says *which
way* the market leans, confidence says *how much to trust that read*.

Formula:
    agreement_pct = (sum of factor weights whose direction agrees with the
                      market direction) / (sum of all factor weights) * 100
    avg_strength  = weighted average of each factor's `strength`
                     (0-100, how far that factor sits from its own neutral)
    confidence    = clamp(0.6 * agreement_pct + 0.4 * avg_strength)

Both inputs are pure functions of the already-computed `FactorScore`s, so
confidence is fully reproducible from the same market data.
"""

from app.ai_engine.types import Direction, FactorScore, clamp

AGREEMENT_WEIGHT = 0.6
STRENGTH_WEIGHT = 0.4


def compute_confidence(
    factors: dict[str, FactorScore],
    weights: dict[str, float],
    market_direction: Direction,
) -> float:
    total_weight = sum(weights.values())
    if total_weight <= 0:
        return 0.0

    agreeing_weight = sum(
        weight for name, weight in weights.items() if weight > 0 and factors[name].direction == market_direction
    )
    agreement_pct = clamp(agreeing_weight / total_weight * 100)

    avg_strength = clamp(sum(factors[name].strength * weight for name, weight in weights.items()) / total_weight)

    return clamp(AGREEMENT_WEIGHT * agreement_pct + STRENGTH_WEIGHT * avg_strength)
