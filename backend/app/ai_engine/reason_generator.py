"""Reason Generator.

Merges every scoring module's reasons into one ordered, de-duplicated
list — highest-weight factors first, since those are the ones that moved
the Market Score the most. Guarantees at least `min_reasons` entries (the
spec requires a minimum of 5 per decision) by padding with generic,
clearly-labeled fallback context if the underlying factors didn't produce
enough on their own (e.g. a symbol with very little backfilled history).
"""

from app.ai_engine.types import FactorScore

MIN_REASONS = 5

_FALLBACK_REASONS = (
    "Limited historical data available for this symbol/timeframe — signal confidence "
    "may improve as more candles accumulate",
    "Some factors are still warming up (indicators like EMA200 need a long lookback " "before they produce a reading)",
    "Treat this analysis as provisional until more market history has been observed",
)


def generate_reasons(
    factors: dict[str, FactorScore], weights: dict[str, float], min_reasons: int = MIN_REASONS
) -> list[str]:
    ordered_names = sorted(factors.keys(), key=lambda name: weights.get(name, 0.0), reverse=True)

    reasons: list[str] = []
    seen: set[str] = set()
    for name in ordered_names:
        for reason in factors[name].reasons:
            if reason not in seen:
                reasons.append(reason)
                seen.add(reason)

    fallback_idx = 0
    while len(reasons) < min_reasons and fallback_idx < len(_FALLBACK_REASONS):
        fallback = _FALLBACK_REASONS[fallback_idx]
        if fallback not in seen:
            reasons.append(fallback)
            seen.add(fallback)
        fallback_idx += 1

    return reasons
