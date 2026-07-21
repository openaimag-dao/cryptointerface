"""LLM Explanation API — see app/intelligence/llm/explanation.py.

Computes live for whatever symbol is requested (unlike the Dashboard
Intelligence Card, which reads the scheduler's cached anchor-symbol
report to avoid a Claude call on every dashboard poll — see
app/intelligence/scheduler/tasks.py).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.intelligence.llm.explanation import build_llm_explanation
from app.schemas.llm import LlmExplanationOut
from app.services.llm_repository import insert_llm_report
from app.utils.timeframes import TIMEFRAME_SECONDS

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.get("/explanation/{symbol}", response_model=LlmExplanationOut)
async def get_explanation(
    symbol: str,
    interval: str = Query("1h", description="One of: " + ", ".join(TIMEFRAME_SECONDS)),
    db: AsyncSession = Depends(get_db),
) -> LlmExplanationOut:
    if interval not in TIMEFRAME_SECONDS:
        raise HTTPException(status_code=400, detail=f"Unsupported interval: {interval}")

    explanation = await build_llm_explanation(db, symbol.upper(), interval)
    if explanation is None:
        raise HTTPException(status_code=404, detail=f"No candle history yet for {symbol} {interval}")
    await insert_llm_report(db, explanation)

    return LlmExplanationOut(
        symbol=explanation.symbol,
        interval=explanation.interval,
        timestamp=explanation.timestamp,
        direction=explanation.direction,
        confidence=round(explanation.confidence, 1),
        summary=explanation.summary,
        key_drivers=explanation.key_drivers,
        risks=explanation.risks,
        opportunities=explanation.opportunities,
        assets_affected=explanation.assets_affected,
    )
