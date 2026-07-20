"""Persistence for AI Decision Engine runs — always an append, never an upsert."""

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
