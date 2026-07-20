from app.schemas.base import CamelModel


class Candle(CamelModel):
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class CandleUpdate(CamelModel):
    """A single in-progress or just-closed candle, pushed over WebSocket."""

    symbol: str
    interval: str
    candle: Candle
    is_closed: bool
