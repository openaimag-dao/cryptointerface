from app.backtesting.models.trade import ClosedTrade
from app.backtesting.performance import PROFIT_FACTOR_CAP, compute_performance_metrics


def _trade(pnl: float, pnl_percent: float, duration: int = 3600, direction: str = "LONG") -> ClosedTrade:
    return ClosedTrade(
        symbol="TESTUSDT",
        direction=direction,
        entry_time=0,
        entry_price=100.0,
        exit_time=duration,
        exit_price=100.0 + pnl,
        quantity=1.0,
        pnl=pnl,
        pnl_percent=pnl_percent,
        exit_reason="TP1" if pnl > 0 else "SL",
        duration_seconds=duration,
        decision_score=60.0,
        confidence=55.0,
        planned_risk_reward=1.5,
    )


def test_compute_performance_metrics_empty_trades():
    metrics = compute_performance_metrics([], initial_balance=10_000.0)
    assert metrics.total_trades == 0
    assert metrics.win_rate == 0.0
    assert metrics.profit_factor == 0.0


def test_compute_performance_metrics_all_wins_caps_profit_factor():
    trades = [_trade(100.0, 1.0), _trade(50.0, 0.5)]
    metrics = compute_performance_metrics(trades, initial_balance=10_000.0)

    assert metrics.total_trades == 2
    assert metrics.winning_trades == 2
    assert metrics.losing_trades == 0
    assert metrics.gross_loss == 0.0
    assert metrics.profit_factor == PROFIT_FACTOR_CAP


def test_compute_performance_metrics_mixed_trades():
    trades = [_trade(200.0, 2.0), _trade(-100.0, -1.0), _trade(50.0, 0.5), _trade(-50.0, -0.5)]
    metrics = compute_performance_metrics(trades, initial_balance=10_000.0)

    assert metrics.total_trades == 4
    assert metrics.winning_trades == 2
    assert metrics.losing_trades == 2
    assert metrics.win_rate == 50.0
    assert metrics.loss_rate == 50.0
    assert metrics.gross_profit == 250.0
    assert metrics.gross_loss == -150.0
    assert metrics.net_profit == 100.0
    assert abs(metrics.profit_factor - (250.0 / 150.0)) < 1e-9
    assert metrics.avg_win == 125.0
    assert metrics.avg_loss == -75.0
    assert abs(metrics.total_return_percent - 1.0) < 1e-9  # 100 / 10000 * 100


def test_compute_performance_metrics_expectancy_matches_formula():
    trades = [_trade(100.0, 1.0), _trade(-40.0, -0.4)]
    metrics = compute_performance_metrics(trades, initial_balance=10_000.0)

    expected = (metrics.win_rate / 100.0) * metrics.avg_win + (metrics.loss_rate / 100.0) * metrics.avg_loss
    assert abs(metrics.expectancy - expected) < 1e-9


def test_compute_performance_metrics_avg_trade_duration():
    trades = [_trade(10.0, 0.1, duration=3600), _trade(-10.0, -0.1, duration=7200)]
    metrics = compute_performance_metrics(trades, initial_balance=10_000.0)
    assert metrics.avg_trade_duration_seconds == 5400.0
