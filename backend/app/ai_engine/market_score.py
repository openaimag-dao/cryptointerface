"""Aggregates every scoring module into one weighted Market Score.

Weights are fixed constants (not learned, not random) so the aggregate is
as reproducible and auditable as each individual factor. `macro`, `news`,
and `whales` all carry real weight now (Sprint 4) — macro/news moved off
their Sprint 3 stub weight, and `whales` is an entirely new factor (no
stub existed for it) at a smaller weight to reflect its narrower coverage
(only ETH/LINK have an Ethereum footprint — see `scoring/whales.py`).
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
from app.ai_engine.scoring.whales import score_whales
from app.ai_engine.types import Direction, FactorScore, clamp, direction_from_score

# Must sum to 1.0. Trend/momentum/structure carry the most weight since
# they're the most predictive, well-established technical factors;
# volatility is intentionally low-weighted since it's directionally
# ambiguous on its own. macro/news/whales all carry real weight (Sprint 4)
# — each technical factor gave up another small slice to fund `whales`,
# same rebalancing pattern used for macro and news earlier in this sprint.
FACTOR_WEIGHTS: dict[str, float] = {
    "trend": 0.16,
    "momentum": 0.13,
    "structure": 0.14,
    "oi": 0.12,
    "volume": 0.09,
    "funding": 0.08,
    "volatility": 0.05,
    "macro": 0.09,
    "news": 0.08,
    "whales": 0.06,
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
        "macro": score_macro(ctx.macro_snapshot),
        "news": score_news(ctx.news_snapshot),
        "whales": score_whales(ctx.whale_snapshot),
    }

    weighted_sum = sum(factors[name].score * weight for name, weight in FACTOR_WEIGHTS.items())
    score = clamp(weighted_sum)
    direction = direction_from_score(score)

    return MarketScoreResult(score=score, direction=direction, factors=factors, weights=dict(FACTOR_WEIGHTS))
