from typing import Literal

from pydantic import BaseModel

LiquidationSide = Literal["LONG", "SHORT"]


class LiquidationEvent(BaseModel):
    id: str
    symbol: str
    side: LiquidationSide
    amount_usd: float
    price: float
    exchange: str
    timestamp: str


class LiquidationHeatmapCell(BaseModel):
    price: float
    intensity: float
