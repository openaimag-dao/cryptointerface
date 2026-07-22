"""Dashboard "Market Intelligence" card — see schemas/dashboard_intelligence.py
for why overall_score and sentiment_score are two different numbers.

`ai_explanation` reads the scheduler's cached report for
`LLM_EXPLANATION_ANCHOR_SYMBOL` (see app/intelligence/scheduler/tasks.py)
rather than calling Claude inline, so this endpoint stays cheap enough
for the Dashboard to poll it directly.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.session import get_db
from app.intelligence.sentiment.engine import compute_sentiment
from app.schemas.dashboard_intelligence import DashboardIntelligence
from app.schemas.llm import LlmExplanationOut
from app.services.llm_repository import get_latest_llm_report
from app.services.sentiment_repository import insert_sentiment_score
from app.utils.timeframes import TIMEFRAME_SECONDS

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
settings = get_settings()


@router.get("/intelligence", response_model=DashboardIntelligence)
async def get_dashboard_intelligence(
    symbol: str = Query(default=None, description="Defaults to the first configured watchlist symbol"),
    interval: str = Query("1h", description="One of: " + ", ".join(TIMEFRAME_SECONDS)),
    db: AsyncSession = Depends(get_db),
) -> DashboardIntelligence:
    if interval not in TIMEFRAME_SECONDS:
        raise HTTPException(status_code=400, detail=f"Unsupported interval: {interval}")
    symbol = (symbol or settings.symbol_list[0]).upper()

    result = await compute_sentiment(db, symbol, interval)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No candle history yet for {symbol} {interval}")
    await insert_sentiment_score(db, result)

    report = await get_latest_llm_report(db, settings.llm_explanation_anchor_symbol, interval)
    ai_explanation = None
    if report is not None:
        ai_explanation = LlmExplanationOut(
            symbol=report.symbol,
            interval=report.interval,
            timestamp=report.time,
            direction=report.direction,
            confidence=round(report.confidence, 1),
            summary=report.summary,
            key_drivers=report.key_drivers,
            risks=report.risks,
            opportunities=report.opportunities,
            assets_affected=report.assets_affected,
        )

    return DashboardIntelligence(
        symbol=result.symbol,
        interval=result.interval,
        overall_score=round(result.breakdown["technical"].score, 1),
        direction=result.direction,
        macro_score=round(result.breakdown["macro"].score, 1),
        news_score=round(result.breakdown["news"].score, 1),
        whale_score=round(result.breakdown["whales"].score, 1),
        liquidation_score=round(result.breakdown["liquidations"].score, 1),
        sentiment_score=round(result.overall_score, 1),
        last_updated=datetime.now(UTC).isoformat(),
        ai_explanation=ai_explanation,
    )
