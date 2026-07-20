from pydantic import BaseModel

from app.models.market import Direction


class AiSignal(BaseModel):
    id: str
    symbol: str
    direction: Direction
    confidence: int
    entry: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    risk_reward: float
    reasons: list[str]
    created_at: str
    timeframe: str


class AiAnalysis(BaseModel):
    symbol: str
    ai_score: int
    direction: Direction
    confidence: int
    reasons: list[str]
    entry: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    risk: float
    reward: float
