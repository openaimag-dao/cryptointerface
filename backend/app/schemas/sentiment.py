from app.schemas.base import CamelModel
from app.schemas.market import Direction


class SentimentCategory(CamelModel):
    score: float
    direction: Direction
    confidence: float
    reasons: list[str]


class SentimentSnapshot(CamelModel):
    symbol: str
    interval: str
    timestamp: int
    overall_score: float
    confidence: float
    direction: Direction
    breakdown: dict[str, SentimentCategory]
    reasons: list[str]
