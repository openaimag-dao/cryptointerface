from app.backtesting.models.trade import ClosedTrade
from app.backtesting.risk_metrics import RECOVERY_FACTOR_CAP, compute_risk_metrics


def _trade(entry_time: int, exit_time: int, pnl: float, pnl_percent: float, rr: float = 1.5) -> ClosedTrade:
    return ClosedTrade(
        symbol="TESTUSDT",
        direction="LONG",
        entry_time=entry_time,
        entry_price=100.0,
        exit_time=exit_time,
        exit_price=100.0 + pnl,
        quantity=1.0,
        pnl=pnl,
        pnl_percent=pnl_percent,
        exit_reason="TP1" if pnl > 0 else "SL",
        duration_seconds=exit_time - entry_time,
        decision_score=60.0,
        confidence=55.0,
        planned_risk_reward=rr,
    )


def test_compute_risk_metrics_no_trades_returns_flat_result():
    metrics = compute_risk_metrics([], initial_balance=10_000.0, period_days=30)
    assert metrics.max_drawdown_percent == 0.0
    assert metrics.final_balance == 10_000.0
    assert metrics.peak_balance == 10_000.0


def test_compute_risk_metrics_monotonic_gains_have_zero_drawdown():
    trades = [
        _trade(0, 3600, 100.0, 1.0),
        _trade(3600, 7200, 200.0, 1.9),
        _trade(7200, 10800, 150.0, 1.4),
    ]
    metrics = compute_risk_metrics(trades, initial_balance=10_000.0, period_days=30)
    assert metrics.max_drawdown_percent == 0.0
    assert metrics.recovery_factor == RECOVERY_FACTOR_CAP
    assert metrics.final_balance == 10_450.0


def test_compute_risk_metrics_drawdown_detected_after_a_loss():
    trades = [
        _trade(0, 3600, 1000.0, 10.0),
        _trade(3600, 7200, -500.0, -4.5),
        _trade(7200, 10800, 100.0, 0.9),
    ]
    metrics = compute_risk_metrics(trades, initial_balance=10_000.0, period_days=30)
    # Peak 11000 -> trough 10500 -> 500/11000 = 4.545%
    assert metrics.max_drawdown_percent > 0.0
    assert metrics.max_drawdown_duration_seconds == 3600
    assert metrics.recovery_factor > 0.0
    assert metrics.recovery_factor < RECOVERY_FACTOR_CAP


def test_compute_risk_metrics_avg_risk_reward_matches_input():
    trades = [_trade(0, 3600, 10.0, 0.1, rr=1.5), _trade(3600, 7200, 20.0, 0.2, rr=2.5)]
    metrics = compute_risk_metrics(trades, initial_balance=10_000.0, period_days=30)
    assert abs(metrics.avg_risk_reward - 2.0) < 1e-9


def test_compute_risk_metrics_sharpe_zero_when_no_variance():
    trades = [_trade(i * 3600, (i + 1) * 3600, 10.0, 0.1) for i in range(5)]
    metrics = compute_risk_metrics(trades, initial_balance=10_000.0, period_days=30)
    # Identical pnl_percent every trade -> zero stdev -> Sharpe defined as 0.0, not NaN/inf
    assert metrics.sharpe_ratio == 0.0
    assert metrics.sortino_ratio == 0.0


def test_compute_risk_metrics_deterministic_same_input_same_output():
    trades = [_trade(0, 3600, 50.0, 0.5), _trade(3600, 7200, -20.0, -0.2)]
    first = compute_risk_metrics(trades, initial_balance=10_000.0, period_days=90)
    second = compute_risk_metrics(trades, initial_balance=10_000.0, period_days=90)
    assert first == second
