from app.schemas.base import CamelModel
from app.schemas.market import Direction


class LlmExplanationOut(CamelModel):
    symbol: str
    interval: str
    timestamp: int
    direction: Direction
    confidence: float
    summary: str
    key_drivers: list[str]
    risks: list[str]
    opportunities: list[str]
    assets_affected: list[str]
