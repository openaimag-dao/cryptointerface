from app.schemas.base import CamelModel
from app.schemas.market import Direction


class AiSignal(CamelModel):
    """A single actionable AI signal — one watchlist symbol's real Decision
    Engine output, included only when its direction is LONG or SHORT (a
    WAIT read isn't a "signal"). See `app/api/signals.py`."""

    id: str
    symbol: str
    direction: Direction
    confidence: float
    entry: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    risk_reward: float
    reasons: list[str]
    created_at: str
    timeframe: str
