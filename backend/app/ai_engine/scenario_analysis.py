"""Scenario Analysis (Sprint 8 spec).

Three scenarios — Bullish / Neutral / Bearish — each with a probability,
a list of conditions, and price targets. Probabilities are a
**deterministic function of the Decision Engine's own outputs**, never
random:

- `confidence` sets how much probability mass is "inconclusive"
  (Neutral) — low confidence means most of the mass sits in Neutral.
- The remaining mass (`confidence`) splits between Bullish/Bearish in
  proportion to how far `market_score` leans from its own neutral
  midpoint (50).

Conditions and targets are template strings/price levels built from the
same `FactorScore`s and ATR/structure levels the Decision Engine and
Risk Engine already compute — no new indicators, no invented numbers.
"""

from dataclasses import dataclass

from app.ai_engine.decision_engine import AIDecision
from app.ai_engine.market_context import MarketContext
from app.ai_engine.types import clamp, last_valid
from app.services.indicators.atr import atr

ATR_PERIOD = 14
TARGET_ATR_MULTIPLIER_NEAR = 2.0
TARGET_ATR_MULTIPLIER_FAR = 4.0
MAX_STRUCTURE_ATR_DISTANCE = 3.0


@dataclass(frozen=True)
class Scenario:
    label: str  # "BULLISH" | "NEUTRAL" | "BEARISH"
    probability: float  # 0-100; the three scenarios sum to 100
    conditions: list[str]
    targets: list[float]


def _numeric_or_none(value: object) -> float | None:
    return float(value) if isinstance(value, int | float) and not isinstance(value, bool) else None


def _scenario_probabilities(market_score: float, confidence: float) -> tuple[float, float, float]:
    """Returns (bullish_pct, neutral_pct, bearish_pct), always summing to 100."""
    lean = clamp((market_score - 50.0) / 50.0, -1.0, 1.0)  # -1 (bearish) .. +1 (bullish)
    neutral_pct = clamp(100.0 - confidence)
    directional_mass = 100.0 - neutral_pct
    bullish_share = (lean + 1.0) / 2.0  # 0..1
    bullish_pct = directional_mass * bullish_share
    bearish_pct = directional_mass - bullish_pct
    return bullish_pct, neutral_pct, bearish_pct


def _bullish_conditions(decision: AIDecision, resistance: float | None) -> list[str]:
    trend = decision.factors["trend"]
    momentum = decision.factors["momentum"]
    conditions = [
        f"Price breaks and holds above resistance near {resistance:.6g}"
        if resistance is not None
        else "Price makes a new local high with rising volume",
        "Trend factor stays bullish" if trend.direction == "LONG" else "Trend factor flips bullish",
        "Momentum factor stays bullish" if momentum.direction == "LONG" else "Momentum factor turns bullish",
    ]
    return conditions


def _bearish_conditions(decision: AIDecision, support: float | None) -> list[str]:
    trend = decision.factors["trend"]
    momentum = decision.factors["momentum"]
    conditions = [
        f"Price breaks and holds below support near {support:.6g}"
        if support is not None
        else "Price makes a new local low with rising volume",
        "Trend factor stays bearish" if trend.direction == "SHORT" else "Trend factor flips bearish",
        "Momentum factor stays bearish" if momentum.direction == "SHORT" else "Momentum factor turns bearish",
    ]
    return conditions


def _neutral_conditions(support: float | None, resistance: float | None) -> list[str]:
    if support is not None and resistance is not None:
        return [
            f"Price stays range-bound between support ({support:.6g}) and resistance ({resistance:.6g})",
            "No factor gathers enough one-sided weight to push confidence past the action threshold",
        ]
    return ["Price continues chopping without a clear break of recent structure"]


def analyze_scenarios(ctx: MarketContext, decision: AIDecision) -> list[Scenario]:
    structure = decision.factors["structure"]
    support = _numeric_or_none(structure.details.get("nearest_support"))
    resistance = _numeric_or_none(structure.details.get("nearest_resistance"))

    price = ctx.last_close
    atr_last = last_valid(atr(ctx.highs, ctx.lows, ctx.closes, ATR_PERIOD))

    bullish_pct, neutral_pct, bearish_pct = _scenario_probabilities(decision.market_score, decision.confidence)

    bullish_near = (
        resistance
        if resistance is not None and atr_last and 0 < resistance - price <= MAX_STRUCTURE_ATR_DISTANCE * atr_last
        else (price + TARGET_ATR_MULTIPLIER_NEAR * atr_last if atr_last else price)
    )
    bullish_far = price + TARGET_ATR_MULTIPLIER_FAR * atr_last if atr_last else price
    bearish_near = (
        support
        if support is not None and atr_last and 0 < price - support <= MAX_STRUCTURE_ATR_DISTANCE * atr_last
        else (price - TARGET_ATR_MULTIPLIER_NEAR * atr_last if atr_last else price)
    )
    bearish_far = price - TARGET_ATR_MULTIPLIER_FAR * atr_last if atr_last else price

    neutral_targets = [level for level in (support, resistance) if level is not None]

    return [
        Scenario(
            label="BULLISH",
            probability=round(bullish_pct, 1),
            conditions=_bullish_conditions(decision, resistance),
            targets=[round(bullish_near, 6), round(bullish_far, 6)],
        ),
        Scenario(
            label="NEUTRAL",
            probability=round(neutral_pct, 1),
            conditions=_neutral_conditions(support, resistance),
            targets=[round(level, 6) for level in neutral_targets],
        ),
        Scenario(
            label="BEARISH",
            probability=round(bearish_pct, 1),
            conditions=_bearish_conditions(decision, support),
            targets=[round(bearish_near, 6), round(bearish_far, 6)],
        ),
    ]
