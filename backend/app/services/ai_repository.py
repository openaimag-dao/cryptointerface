"""Persistence for AI Decision Engine runs — always an append, never an upsert."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_engine.decision_engine import AIDecision
from app.models.ai_analysis import AIAnalysis


async def insert_ai_analysis(db: AsyncSession, decision: AIDecision) -> None:
    risk = decision.risk
    row = AIAnalysis(
        symbol=decision.symbol,
        interval=decision.interval,
        time=decision.timestamp,
        score=decision.market_score,
        confidence=decision.confidence,
        direction=decision.direction,
        entry=risk.entry if risk else None,
        stop=risk.stop if risk else None,
        tp1=risk.tp1 if risk else None,
        tp2=risk.tp2 if risk else None,
        tp3=risk.tp3 if risk else None,
        risk_reward=risk.risk_reward_tp2 if risk else None,
    )
    db.add(row)
    await db.commit()


async def get_recent_analysis(db: AsyncSession, symbol: str, interval: str, limit: int = 50) -> list[AIAnalysis]:
    """Most recent `limit` persisted decisions, ascending (oldest -> newest)."""
    stmt = (
        select(AIAnalysis)
        .where(AIAnalysis.symbol == symbol, AIAnalysis.interval == interval)
        .order_by(AIAnalysis.time.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    rows.reverse()
    return rows
