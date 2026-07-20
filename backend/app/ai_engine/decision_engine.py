"""Decision Engine — the top-level entry point of the AI engine.

`decide_direction` is the strict LONG/SHORT/WAIT gate: the Market Score's
raw direction only becomes an actionable LONG/SHORT if confidence clears
`MIN_CONFIDENCE_FOR_ACTION`; otherwise it downgrades to WAIT rather than
act on a low-conviction read. There is no fourth value and no numeric
output from this function — analysis only, no order is ever placed.

`analyze_market` is the orchestration path the API layer calls: it runs
every scoring module (via `market_score.py`), scores confidence, gates
the final direction, generates reasons, and computes a risk plan — all in
one deterministic pass over a single `MarketContext` snapshot.
"""

from dataclasses import dataclass

from app.ai_engine.confidence_engine import compute_confidence
from app.ai_engine.market_context import MarketContext
from app.ai_engine.market_score import compute_market_score
from app.ai_engine.reason_generator import generate_reasons
from app.ai_engine.risk_engine import RiskPlan, compute_risk_plan
from app.ai_engine.types import Direction, FactorScore

# Below this confidence, the engine will not commit to a LONG/SHORT call
# even if the Market Score leans that way — it downgrades to WAIT instead.
MIN_CONFIDENCE_FOR_ACTION = 45.0


def decide_direction(market_direction: Direction, confidence: float) -> Direction:
    if market_direction == "WAIT":
        return "WAIT"
    if confidence < MIN_CONFIDENCE_FOR_ACTION:
        return "WAIT"
    return market_direction


@dataclass(frozen=True)
class AIDecision:
    symbol: str
    interval: str
    timestamp: int
    market_score: float
    confidence: float
    direction: Direction
    reasons: list[str]
    factors: dict[str, FactorScore]
    weights: dict[str, float]
    risk: RiskPlan | None


def analyze_market(ctx: MarketContext) -> AIDecision:
    market_result = compute_market_score(ctx)
    confidence = compute_confidence(market_result.factors, market_result.weights, market_result.direction)
    direction = decide_direction(market_result.direction, confidence)
    reasons = generate_reasons(market_result.factors, market_result.weights)
    risk = compute_risk_plan(direction, ctx, market_result.factors["structure"])

    return AIDecision(
        symbol=ctx.symbol,
        interval=ctx.interval,
        timestamp=ctx.last_candle_time,
        market_score=market_result.score,
        confidence=confidence,
        direction=direction,
        reasons=reasons,
        factors=market_result.factors,
        weights=market_result.weights,
        risk=risk,
    )
