from app.schemas.base import CamelModel
from app.schemas.market import Direction


class Position(CamelModel):
    id: str
    symbol: str
    direction: Direction
    size: float
    entry_price: float
    mark_price: float
    pnl: float
    pnl_percent: float
    leverage: int
    opened_at: str


class TradeHistoryItem(CamelModel):
    id: str
    symbol: str
    direction: Direction
    entry_price: float
    exit_price: float
    pnl: float
    pnl_percent: float
    opened_at: str
    closed_at: str


class PortfolioSummary(CamelModel):
    balance: float
    equity: float
    total_pnl: float
    total_pnl_percent: float
    win_rate: float
    total_trades: int
    open_positions: list[Position]
    history: list[TradeHistoryItem]
