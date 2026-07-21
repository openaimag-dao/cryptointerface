"""Persistence for LLM explanations (`app/intelligence/llm/`)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.llm.explanation import LlmExplanation
from app.models.llm_report import LlmReport


async def insert_llm_report(db: AsyncSession, explanation: LlmExplanation) -> None:
    db.add(
        LlmReport(
            symbol=explanation.symbol,
            interval=explanation.interval,
            time=explanation.timestamp,
            direction=explanation.direction,
            confidence=explanation.confidence,
            summary=explanation.summary,
            key_drivers=explanation.key_drivers,
            risks=explanation.risks,
            opportunities=explanation.opportunities,
            assets_affected=explanation.assets_affected,
        )
    )
    await db.commit()


async def get_latest_llm_report(db: AsyncSession, symbol: str, interval: str) -> LlmReport | None:
    stmt = (
        select(LlmReport)
        .where(LlmReport.symbol == symbol, LlmReport.interval == interval)
        .order_by(LlmReport.time.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalars().first()
