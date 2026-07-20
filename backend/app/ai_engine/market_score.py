"""Aggregates every scoring module into one weighted Market Score.

Weights are fixed constants (not learned, not random) so the aggregate is
as reproducible and auditable as each individual factor. `macro` and
`news` are Sprint 4 stubs and carry zero weight today — wiring real data
into them later only requires bumping their weight here, nothing else in
the engine has to change.
"""

from dataclasses import dataclass

from app.ai_engine.market_context import MarketContext
from app.ai_engine.scoring.funding import score_funding
from app.ai_engine.scoring.macro import score_macro
from app.ai_engine.scoring.momentum import score_momentum
from app.ai_engine.scoring.news import score_news
from app.ai_engine.scoring.oi import score_oi
from app.ai_engine.scoring.structure import score_structure
from app.ai_engine.scoring.trend import score_trend
from app.ai_engine.scoring.volatility import score_volatility
from app.ai_engine.scoring.volume import score_volume
from app.ai_engine.types import Direction, FactorScore, clamp, direction_from_score

# Must sum to 1.0. Trend/momentum/structure carry the most weight since
# they're the most predictive, well-established technical factors;
# volatility is intentionally low-weighted since it's directionally
# ambiguous on its own. macro/news are Sprint 4 stubs at zero weight.
FACTOR_WEIGHTS: dict[str, float] = {
    "trend": 0.22,
    "momentum": 0.18,
    "structure": 0.18,
    "oi": 0.15,
    "volume": 0.12,
    "funding": 0.10,
    "volatility": 0.05,
    "macro": 0.00,
    "news": 0.00,
}


@dataclass(frozen=True)
class MarketScoreResult:
    score: float
    direction: Direction
    factors: dict[str, FactorScore]
    weights: dict[str, float]


def compute_market_score(ctx: MarketContext) -> MarketScoreResult:
    factors: dict[str, FactorScore] = {
        "trend": score_trend(ctx.closes, ctx.highs, ctx.lows),
        "momentum": score_momentum(ctx.closes),
        "volatility": score_volatility(ctx.closes, ctx.highs, ctx.lows),
        "volume": score_volume(ctx.closes, ctx.highs, ctx.lows, ctx.volumes),
        "structure": score_structure(ctx.closes, ctx.highs, ctx.lows),
        "funding": score_funding(ctx.funding_history),
        "oi": score_oi(ctx.closes, ctx.oi_history),
        "macro": score_macro(),
        "news": score_news(),
    }

    weighted_sum = sum(factors[name].score * weight for name, weight in FACTOR_WEIGHTS.items())
    score = clamp(weighted_sum)
    direction = direction_from_score(score)

    return MarketScoreResult(score=score, direction=direction, factors=factors, weights=dict(FACTOR_WEIGHTS))
