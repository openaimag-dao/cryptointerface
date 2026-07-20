"""AI Decision Engine API.

Analysis only — these endpoints never place orders or execute trades.
Each call recomputes a fresh, deterministic analysis from the latest
candle history (see `app.ai_engine.decision_engine.analyze_market`) and
persists it to `ai_analysis` for history/audit.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_engine.decision_engine import AIDecision, analyze_market
from app.ai_engine.market_context import build_market_context
from app.ai_engine.risk_engine import RiskPlan
from app.ai_engine.types import FactorScore
from app.database.session import get_db
from app.schemas.ai import AIDecisionOut, AIReasonsOut, AIRiskOut, AIScoreOut, FactorScoreOut, RiskPlanOut
from app.services.ai_repository import insert_ai_analysis
from app.utils.timeframes import TIMEFRAME_SECONDS

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _factor_out(factor: FactorScore) -> FactorScoreOut:
    return FactorScoreOut(
        name=factor.name,
        score=factor.score,
        direction=factor.direction,
        strength=factor.strength,
        reasons=factor.reasons,
        details=factor.details,
    )


def _risk_out(risk: RiskPlan | None) -> RiskPlanOut | None:
    if risk is None:
        return None
    return RiskPlanOut(
        direction=risk.direction,
        entry=risk.entry,
        stop=risk.stop,
        tp1=risk.tp1,
        tp2=risk.tp2,
        tp3=risk.tp3,
        risk_per_unit=risk.risk_per_unit,
        risk_reward_tp1=risk.risk_reward_tp1,
        risk_reward_tp2=risk.risk_reward_tp2,
        risk_reward_tp3=risk.risk_reward_tp3,
    )


async def _run_analysis(symbol: str, interval: str, db: AsyncSession) -> AIDecision:
    if interval not in TIMEFRAME_SECONDS:
        raise HTTPException(status_code=400, detail=f"Unsupported interval: {interval}")

    ctx = await build_market_context(db, symbol.upper(), interval)
    if ctx is None:
        raise HTTPException(status_code=404, detail=f"No candle history yet for {symbol} {interval}")

    decision = analyze_market(ctx)
    await insert_ai_analysis(db, decision)
    return decision


@router.get("/decision/{symbol}", response_model=AIDecisionOut)
async def get_decision(
    symbol: str,
    interval: str = Query("1h", description="One of: " + ", ".join(TIMEFRAME_SECONDS)),
    db: AsyncSession = Depends(get_db),
) -> AIDecisionOut:
    decision = await _run_analysis(symbol, interval, db)
    return AIDecisionOut(
        symbol=decision.symbol,
        interval=decision.interval,
        timestamp=decision.timestamp,
        market_score=decision.market_score,
        confidence=decision.confidence,
        direction=decision.direction,
        reasons=decision.reasons,
        factors={name: _factor_out(factor) for name, factor in decision.factors.items()},
        risk=_risk_out(decision.risk),
    )


@router.get("/score/{symbol}", response_model=AIScoreOut)
async def get_score(
    symbol: str,
    interval: str = Query("1h", description="One of: " + ", ".join(TIMEFRAME_SECONDS)),
    db: AsyncSession = Depends(get_db),
) -> AIScoreOut:
    decision = await _run_analysis(symbol, interval, db)
    return AIScoreOut(
        symbol=decision.symbol,
        interval=decision.interval,
        timestamp=decision.timestamp,
        market_score=decision.market_score,
        confidence=decision.confidence,
        direction=decision.direction,
        factors={name: _factor_out(factor) for name, factor in decision.factors.items()},
    )


@router.get("/reasons/{symbol}", response_model=AIReasonsOut)
async def get_reasons(
    symbol: str,
    interval: str = Query("1h", description="One of: " + ", ".join(TIMEFRAME_SECONDS)),
    db: AsyncSession = Depends(get_db),
) -> AIReasonsOut:
    decision = await _run_analysis(symbol, interval, db)
    return AIReasonsOut(
        symbol=decision.symbol,
        interval=decision.interval,
        timestamp=decision.timestamp,
        direction=decision.direction,
        reasons=decision.reasons,
    )


@router.get("/risk/{symbol}", response_model=AIRiskOut)
async def get_risk(
    symbol: str,
    interval: str = Query("1h", description="One of: " + ", ".join(TIMEFRAME_SECONDS)),
    db: AsyncSession = Depends(get_db),
) -> AIRiskOut:
    decision = await _run_analysis(symbol, interval, db)
    return AIRiskOut(
        symbol=decision.symbol,
        interval=decision.interval,
        timestamp=decision.timestamp,
        direction=decision.direction,
        risk=_risk_out(decision.risk),
    )
