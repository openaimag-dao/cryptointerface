from typing import Literal

from app.schemas.base import CamelModel

TradeDirection = Literal["LONG", "SHORT"]
ExitReason = Literal["TP1", "SL", "END_OF_DATA"]
RunStatus = Literal["PENDING", "RUNNING", "COMPLETED", "FAILED"]


class BacktestRunRequest(CamelModel):
    symbol: str
    timeframe: str
    period_days: int
    initial_balance: float = 10_000.0
    commission_bps: float = 4.0
    slippage_bps: float = 2.0
    risk_per_trade_percent: float = 1.0


class PerformanceMetricsOut(CamelModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_return_percent: float
    net_profit: float
    gross_profit: float
    gross_loss: float
    win_rate: float
    loss_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    expectancy: float
    avg_trade_duration_seconds: float


class RiskMetricsOut(CamelModel):
    max_drawdown_percent: float
    max_drawdown_duration_seconds: int
    recovery_factor: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    avg_risk_reward: float
    final_balance: float
    peak_balance: float


class BacktestTradeOut(CamelModel):
    id: str
    symbol: str
    direction: TradeDirection
    entry_time: int
    entry_price: float
    exit_time: int
    exit_price: float
    quantity: float
    pnl: float
    pnl_percent: float
    exit_reason: ExitReason
    duration_seconds: int
    decision_score: float
    confidence: float
    planned_risk_reward: float


class EquityPointOut(CamelModel):
    time: int
    balance: float
    drawdown_percent: float
    cumulative_pnl: float
    trade_count: int


class BacktestRunOut(CamelModel):
    id: str
    symbol: str
    timeframe: str
    period_days: int
    start_time: int
    end_time: int
    status: RunStatus
    strategy_version_name: str
    initial_balance: float
    commission_bps: float
    slippage_bps: float
    error_message: str | None
    started_at: int | None
    completed_at: int | None
    duration_ms: int | None


class BacktestMetricsOut(CamelModel):
    """Just the numbers — what `/metrics/{run_id}` returns. `/report`
    returns this plus the run's own metadata (see `BacktestReportOut`)."""

    performance: PerformanceMetricsOut
    risk: RiskMetricsOut


class BacktestReportOut(CamelModel):
    """Everything about one run in a single payload — what `/report`
    returns, and what `/run` returns immediately after a run completes so
    the frontend doesn't need a second round-trip to show results."""

    run: BacktestRunOut
    performance: PerformanceMetricsOut
    risk: RiskMetricsOut
