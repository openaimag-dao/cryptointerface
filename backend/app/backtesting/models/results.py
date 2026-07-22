from dataclasses import dataclass, field

from app.backtesting.models.trade import ClosedTrade


@dataclass(frozen=True)
class EquityPoint:
    time: int
    balance: float
    drawdown_percent: float
    cumulative_pnl: float
    trade_count: int


@dataclass(frozen=True)
class PerformanceMetrics:
    """See `app/backtesting/performance.py` for how each field is derived."""

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


@dataclass(frozen=True)
class RiskMetrics:
    """See `app/backtesting/risk_metrics.py` for how each field is derived."""

    max_drawdown_percent: float
    max_drawdown_duration_seconds: int
    recovery_factor: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    avg_risk_reward: float
    final_balance: float
    peak_balance: float


@dataclass(frozen=True)
class BacktestRunResult:
    """Everything one completed backtest run produced — what `engine.py`
    returns, and what the API/persistence layers translate into
    `backtest_runs` + `backtest_trades` + `backtest_metrics` + `equity_curve`
    rows."""

    symbol: str
    timeframe: str
    period_days: int
    start_time: int
    end_time: int
    strategy_version_name: str
    trades: list[ClosedTrade]
    equity_curve: list[EquityPoint] = field(repr=False)
    performance: PerformanceMetrics
    risk: RiskMetrics
    bars_analyzed: int
