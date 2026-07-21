"""Sentiment Engine (Sprint 4): blends Technical Analysis (the AI Decision
Engine's own Market Score/Confidence), Macro, Liquidations, News, and
Whales into one overall market read.

This sits *above* `app.ai_engine.market_score` rather than inside it: that
module aggregates a single symbol's technical factors into the Decision
Engine's Market Score; this combines that already-computed technical read
with the broader Sprint-4 inputs. It never feeds back into the Decision
Engine — trading-relevant Direction/Confidence still come from
`app.ai_engine` alone (`/api/ai/*`, `/api/signals`); this is a separate,
explanatory view for the Dashboard Intelligence Card and `/api/sentiment`.

Whales is still a Sprint 4 stub (real on-chain tracking lands in a
follow-up PR) — it contributes a neutral, zero-weighted read so the
overall blend is unaffected until real data lands, the same pattern
`app.ai_engine` used for macro/news in Sprint 3. News is real as of this
PR (RSS ingestion + a deterministic classifier — see
`app/intelligence/news/`).
"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_engine.decision_engine import analyze_market
from app.ai_engine.market_context import build_market_context
from app.ai_engine.scoring.macro import score_macro
from app.ai_engine.scoring.news import score_news
from app.ai_engine.types import Direction, FactorScore, clamp, direction_from_score
from app.intelligence.sentiment.liquidation_factor import score_liquidations
from app.services.market_repository import get_liquidation_totals_24h

# Must sum to 1.0. Technical carries the most weight since it's the only
# category backed by a full deterministic model; Macro/Liquidations/News
# are real-but-narrower signals; Whales is a Sprint 4 stub at zero weight
# until real ingestion lands (see module docstring).
CATEGORY_WEIGHTS: dict[str, float] = {
    "technical": 0.55,
    "macro": 0.20,
    "liquidations": 0.15,
    "news": 0.10,
    "whales": 0.00,
}


@dataclass(frozen=True)
class SentimentFactor:
    """One category's contribution: score/direction/confidence/reasons —
    exactly the shape the Sprint 4 spec asks each module to return."""

    score: float
    direction: Direction
    confidence: float
    reasons: list[str]


@dataclass(frozen=True)
class SentimentResult:
    symbol: str
    interval: str
    timestamp: int
    overall_score: float
    confidence: float
    direction: Direction
    breakdown: dict[str, SentimentFactor]
    reasons: list[str]


def _from_factor_score(factor: FactorScore) -> SentimentFactor:
    """`FactorScore` has no confidence field of its own — `strength` (how
    far the score sits from neutral) is the closest single-factor analog,
    same substitution `reason_generator.py` implicitly relies on."""
    return SentimentFactor(
        score=factor.score, direction=factor.direction, confidence=factor.strength, reasons=factor.reasons
    )


def _whales_stub() -> SentimentFactor:
    return SentimentFactor(
        score=50.0,
        direction="WAIT",
        confidence=0.0,
        reasons=["Whale-wallet tracking is not yet integrated — neutral, zero-weight Sprint 4 stub"],
    )


async def compute_sentiment(db: AsyncSession, symbol: str, interval: str) -> SentimentResult | None:
    """Returns None if there isn't enough candle history yet for the
    Technical factor (same "no data yet" gate as `/api/signals`)."""
    ctx = await build_market_context(db, symbol, interval)
    if ctx is None:
        return None

    decision = analyze_market(ctx)
    technical = SentimentFactor(
        score=decision.market_score,
        direction=decision.direction,
        confidence=decision.confidence,
        reasons=decision.reasons,
    )
    macro = _from_factor_score(score_macro(ctx.macro_snapshot))
    liquidation_totals = await get_liquidation_totals_24h(db)
    liquidations = _from_factor_score(score_liquidations(liquidation_totals))
    news = _from_factor_score(score_news(ctx.news_snapshot))
    whales = _whales_stub()

    breakdown: dict[str, SentimentFactor] = {
        "technical": technical,
        "macro": macro,
        "liquidations": liquidations,
        "news": news,
        "whales": whales,
    }

    overall_score = clamp(sum(breakdown[name].score * weight for name, weight in CATEGORY_WEIGHTS.items()))
    overall_confidence = clamp(sum(breakdown[name].confidence * weight for name, weight in CATEGORY_WEIGHTS.items()))
    overall_direction = direction_from_score(overall_score)

    reasons: list[str] = []
    for name in ("technical", "macro", "liquidations", "news"):
        reasons.extend(breakdown[name].reasons[:2])

    return SentimentResult(
        symbol=symbol,
        interval=interval,
        timestamp=decision.timestamp,
        overall_score=overall_score,
        confidence=overall_confidence,
        direction=overall_direction,
        breakdown=breakdown,
        reasons=reasons,
    )
