"""Drawdown and risk-adjusted-return metrics — the rest of the Sprint 5
spec's "Performance Metrics" section (Max Drawdown, Recovery Factor,
Sharpe/Sortino/Calmar, Risk/Reward). Like `performance.py`, every function
here is pure — no I/O.

Sharpe/Sortino are computed from each trade's `pnl_percent` in trade
sequence, annualized by how many trades this run actually produced per
year — not from a bar-by-bar mark-to-market equity series. The engine's
equity curve only changes value when a trade closes (see
`trade_simulator.py`'s docstring), so a bar-level return series would be
mostly zeros and would understate volatility in a way that doesn't
reflect the strategy's real risk. Documented as a deliberate choice in
`backend/README.md`'s Backtesting Engine section, not an oversight.
"""

from app.backtesting.models.results import RiskMetrics
from app.backtesting.models.trade import ClosedTrade
from app.backtesting.statistics import annualization_factor, downside_deviation, max_drawdown, mean, stdev

# Same rationale as performance.py's PROFIT_FACTOR_CAP — these ratios are
# mathematically undefined (division by zero) rather than infinite when
# there's no drawdown/no return variance; a finite cap keeps every field
# reliably JSON-serializable.
RECOVERY_FACTOR_CAP = 999.0
DAYS_PER_YEAR = 365.0


def compute_risk_metrics(trades: list[ClosedTrade], initial_balance: float, period_days: int) -> RiskMetrics:
    if not trades:
        return RiskMetrics(
            max_drawdown_percent=0.0,
            max_drawdown_duration_seconds=0,
            recovery_factor=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            calmar_ratio=0.0,
            avg_risk_reward=0.0,
            final_balance=initial_balance,
            peak_balance=initial_balance,
        )

    balances = [initial_balance]
    for trade in trades:
        balances.append(balances[-1] + trade.pnl)

    dd_pct, dd_dollar, peak_idx, trough_idx = max_drawdown(balances)

    # balances[0] is "before any trade" (the run's start_time); balances[i]
    # for i >= 1 is the balance right after trades[i-1] closed.
    peak_time = trades[peak_idx - 1].exit_time if peak_idx > 0 else trades[0].entry_time
    trough_time = trades[trough_idx - 1].exit_time if trough_idx > 0 else trades[0].entry_time
    max_dd_duration = max(0, trough_time - peak_time)

    net_profit = balances[-1] - initial_balance
    recovery_factor = (net_profit / dd_dollar) if dd_dollar > 0 else RECOVERY_FACTOR_CAP

    pnl_percents = [t.pnl_percent for t in trades]
    trades_per_year = (len(trades) / period_days) * DAYS_PER_YEAR if period_days > 0 else 0.0
    ann_factor = annualization_factor(trades_per_year)

    avg_return = mean(pnl_percents)
    return_stdev = stdev(pnl_percents)
    sharpe = (avg_return / return_stdev * ann_factor) if return_stdev > 0 else 0.0

    downside_dev = downside_deviation(pnl_percents, target=0.0)
    sortino = (avg_return / downside_dev * ann_factor) if downside_dev > 0 else 0.0

    total_return_percent = (net_profit / initial_balance) * 100.0 if initial_balance > 0 else 0.0
    if period_days > 0 and total_return_percent > -100.0:
        growth = 1.0 + total_return_percent / 100.0
        annualized_return_percent = (growth ** (DAYS_PER_YEAR / period_days) - 1.0) * 100.0
    else:
        annualized_return_percent = 0.0
    calmar = (annualized_return_percent / dd_pct) if dd_pct > 0 else 0.0

    avg_risk_reward = mean([t.planned_risk_reward for t in trades])

    return RiskMetrics(
        max_drawdown_percent=dd_pct,
        max_drawdown_duration_seconds=int(max_dd_duration),
        recovery_factor=recovery_factor,
        sharpe_ratio=sharpe,
        sortino_ratio=sortino,
        calmar_ratio=calmar,
        avg_risk_reward=avg_risk_reward,
        final_balance=balances[-1],
        peak_balance=max(balances),
    )
