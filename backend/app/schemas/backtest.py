from pydantic import BaseModel


class EquityPoint(BaseModel):
    time: int
    value: float


class BacktestRequest(BaseModel):
    strategy: str
    symbol: str
    timeframe: str


class BacktestResult(BaseModel):
    id: str
    strategy: str
    symbol: str
    timeframe: str
    period: str
    total_trades: int
    win_rate: float
    profit_factor: float
    total_return_percent: float
    max_drawdown_percent: float
    sharpe_ratio: float
    equity_curve: list[EquityPoint]
