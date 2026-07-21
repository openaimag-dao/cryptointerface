from typing import Literal

from app.schemas.base import CamelModel

LiquidationSide = Literal["LONG", "SHORT"]


class LiquidationEvent(CamelModel):
    id: str
    symbol: str
    side: LiquidationSide
    amount_usd: float
    price: float
    exchange: str
    timestamp: str


class LiquidationHeatmapCell(CamelModel):
    price: float
    intensity: float


class LiquidationTotals(CamelModel):
    long_usd: float
    short_usd: float


class LiquidationUpdate(CamelModel):
    """Live push over the `liquidation` WebSocket channel — see
    `app/tasks/live_feed.py`'s `_handle_liquidation`."""

    symbol: str
    side: LiquidationSide
    amount_usd: float
    price: float
    exchange: str
    timestamp: int
