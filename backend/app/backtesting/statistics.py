"""Shared statistical helpers used by `performance.py` and `risk_metrics.py`,
plus the Monte Carlo trade-shuffle utility.

Every function here is a pure function over plain numbers — no I/O, no
hidden state — which is what makes the metrics it feeds into
deterministic and independently testable.
"""

import random

import numpy as np

TRADING_DAYS_PER_YEAR = 365.0


def mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else 0.0


def stdev(values: list[float]) -> float:
    """Sample standard deviation (ddof=1) — 0.0 for fewer than 2 points,
    never NaN (numpy's ddof=1 stdev of a single value is NaN, which would
    silently poison every Sharpe/Sortino computation downstream)."""
    if len(values) < 2:
        return 0.0
    return float(np.std(values, ddof=1))


def downside_deviation(returns: list[float], target: float = 0.0) -> float:
    """Standard deviation of only the returns that fell below `target` —
    the Sortino Ratio's denominator: unlike Sharpe, it doesn't penalize
    upside volatility, only the downside kind that actually hurts."""
    downside = [r - target for r in returns if r < target]
    if len(downside) < 2:
        return 0.0
    return float(np.std(downside, ddof=1))


def annualization_factor(trades_per_year: float) -> float:
    """sqrt(N) annualization factor for a return series sampled
    `trades_per_year` times per year — standard Sharpe/Sortino scaling."""
    return float(np.sqrt(trades_per_year)) if trades_per_year > 0 else 0.0


def max_drawdown(balances: list[float]) -> tuple[float, float, int, int]:
    """Walks the equity curve once and returns
    `(max_drawdown_percent, max_drawdown_dollar, peak_index, trough_index)`.
    Drawdown is measured from the running peak, the standard definition —
    not from the starting balance, which would understate a drawdown that
    happens after a big early run-up.
    """
    if not balances:
        return 0.0, 0.0, 0, 0

    peak = balances[0]
    peak_idx = 0
    max_dd_pct = 0.0
    max_dd_dollar = 0.0
    max_dd_peak_idx = 0
    max_dd_trough_idx = 0

    for i, balance in enumerate(balances):
        if balance > peak:
            peak = balance
            peak_idx = i
        drawdown_dollar = peak - balance
        drawdown_pct = (drawdown_dollar / peak * 100.0) if peak > 0 else 0.0
        if drawdown_pct > max_dd_pct:
            max_dd_pct = drawdown_pct
            max_dd_dollar = drawdown_dollar
            max_dd_peak_idx = peak_idx
            max_dd_trough_idx = i

    return max_dd_pct, max_dd_dollar, max_dd_peak_idx, max_dd_trough_idx


def monte_carlo_shuffle(trade_pnls: list[float], n_simulations: int = 200, seed: int = 42) -> list[list[float]]:
    """Architecture for Monte Carlo robustness analysis (Sprint 5 spec:
    "случайная перестановка последовательности сделок без изменения их
    результатов" — random permutation of trade order, values unchanged).

    Returns `n_simulations` reshufflings of the same trade PnL values —
    never invents or alters a single value, only reorders them, so every
    simulated equity curve still ends at the same final balance; only the
    *path* (and therefore the drawdown/Sharpe distribution) differs.

    Deterministic given `seed`: same seed -> byte-identical output every
    time, satisfying the spec's "все вычисления должны быть
    воспроизводимыми" for what is, by definition, a randomized technique.
    Uses a private `random.Random(seed)` instance rather than the module-
    level `random` so this never perturbs any other part of the process's
    random state.
    """
    rng = random.Random(seed)
    simulations: list[list[float]] = []
    for _ in range(n_simulations):
        shuffled = trade_pnls.copy()
        rng.shuffle(shuffled)
        simulations.append(shuffled)
    return simulations


def monte_carlo_drawdown_distribution(
    trade_pnls: list[float], initial_balance: float, n_simulations: int = 200, seed: int = 42
) -> list[float]:
    """For each Monte Carlo reshuffling, the max drawdown percent that
    trade order would have produced — the actual "how bad could my worst
    case have looked" distribution a robustness check cares about."""
    results = []
    for shuffled in monte_carlo_shuffle(trade_pnls, n_simulations=n_simulations, seed=seed):
        balances = [initial_balance]
        for pnl in shuffled:
            balances.append(balances[-1] + pnl)
        dd_pct, _, _, _ = max_drawdown(balances)
        results.append(dd_pct)
    return results
