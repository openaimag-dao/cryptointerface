from app.ai_engine.types import Direction
from app.schemas.base import CamelModel


class FactorScoreOut(CamelModel):
    name: str
    score: float
    direction: Direction
    strength: float
    reasons: list[str]
    details: dict[str, float | str | bool | int]


class RiskPlanOut(CamelModel):
    direction: Direction
    entry: float
    stop: float
    tp1: float
    tp2: float
    tp3: float
    risk_per_unit: float
    risk_reward_tp1: float
    risk_reward_tp2: float
    risk_reward_tp3: float


class AIDecisionOut(CamelModel):
    symbol: str
    interval: str
    timestamp: int
    market_score: float
    confidence: float
    direction: Direction
    reasons: list[str]
    factors: dict[str, FactorScoreOut]
    risk: RiskPlanOut | None


class AIScoreOut(CamelModel):
    symbol: str
    interval: str
    timestamp: int
    market_score: float
    confidence: float
    direction: Direction
    factors: dict[str, FactorScoreOut]


class AIReasonsOut(CamelModel):
    symbol: str
    interval: str
    timestamp: int
    direction: Direction
    reasons: list[str]


class AIRiskOut(CamelModel):
    symbol: str
    interval: str
    timestamp: int
    direction: Direction
    risk: RiskPlanOut | None
