"""Trade-level performance metrics — everything in the Sprint 5 spec's
"Performance Metrics" section except the risk/drawdown-based ones, which
live in `risk_metrics.py`. Every function here is a pure function over a
list of already-closed trades; nothing here touches the database or the
Decision Engine.
"""

from app.backtesting.models.results import PerformanceMetrics
from app.backtesting.models.trade import ClosedTrade
from app.backtesting.statistics import mean

# Reported when there are zero losing trades — Profit Factor is
# mathematically undefined (division by zero) in that case, not
# infinite in any useful sense. A large finite cap keeps every field
# JSON-serializable without a special "null means infinity" contract on
# the API.
PROFIT_FACTOR_CAP = 999.0


def compute_performance_metrics(trades: list[ClosedTrade], initial_balance: float) -> PerformanceMetrics:
    if not trades:
        return PerformanceMetrics(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            total_return_percent=0.0,
            net_profit=0.0,
            gross_profit=0.0,
            gross_loss=0.0,
            win_rate=0.0,
            loss_rate=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            profit_factor=0.0,
            expectancy=0.0,
            avg_trade_duration_seconds=0.0,
        )

    wins = [t.pnl for t in trades if t.pnl > 0]
    losses = [t.pnl for t in trades if t.pnl < 0]  # negative values
    total_trades = len(trades)
    winning_trades = len(wins)
    losing_trades = len(losses)

    net_profit = sum(t.pnl for t in trades)
    gross_profit = sum(wins)
    gross_loss = sum(losses)  # <= 0

    win_rate = winning_trades / total_trades * 100.0
    loss_rate = losing_trades / total_trades * 100.0
    avg_win = mean(wins)
    avg_loss = mean(losses)

    profit_factor = (gross_profit / abs(gross_loss)) if gross_loss < 0 else PROFIT_FACTOR_CAP
    expectancy = (win_rate / 100.0) * avg_win + (loss_rate / 100.0) * avg_loss
    avg_trade_duration_seconds = mean([float(t.duration_seconds) for t in trades])
    total_return_percent = (net_profit / initial_balance) * 100.0 if initial_balance > 0 else 0.0

    return PerformanceMetrics(
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        total_return_percent=total_return_percent,
        net_profit=net_profit,
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        win_rate=win_rate,
        loss_rate=loss_rate,
        avg_win=avg_win,
        avg_loss=avg_loss,
        profit_factor=profit_factor,
        expectancy=expectancy,
        avg_trade_duration_seconds=avg_trade_duration_seconds,
    )
