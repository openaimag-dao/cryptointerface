import pytest

from app.backtesting.models.config import TradeSimulatorConfig
from app.backtesting.models.results import EquityPoint, PerformanceMetrics, RiskMetrics
from app.backtesting.models.trade import ClosedTrade
from app.services.backtest_repository import (
    create_run,
    get_equity_curve,
    get_metrics,
    get_or_create_default_strategy_version,
    get_run,
    get_trades,
    insert_equity_curve,
    insert_metrics,
    insert_trades,
    list_runs,
    list_strategy_versions,
    mark_run_completed,
    mark_run_failed,
    mark_run_running,
)


@pytest.mark.asyncio
async def test_get_or_create_default_strategy_version_is_idempotent(db_session):
    first = await get_or_create_default_strategy_version(db_session)
    second = await get_or_create_default_strategy_version(db_session)

    assert first.id == second.id
    versions = await list_strategy_versions(db_session)
    assert len(versions) == 1
    assert "factor_weights" in first.config


@pytest.mark.asyncio
async def test_create_run_and_status_transitions(db_session):
    version = await get_or_create_default_strategy_version(db_session)
    run = await create_run(
        db_session,
        symbol="TESTUSDT",
        timeframe="1h",
        period_days=30,
        start_time=1000,
        end_time=2000,
        strategy_version_id=version.id,
        simulator_config=TradeSimulatorConfig(),
    )
    assert run.status == "PENDING"

    await mark_run_running(db_session, run.id, started_at=1500)
    fetched = await get_run(db_session, run.id)
    assert fetched.status == "RUNNING"
    assert fetched.started_at == 1500

    await mark_run_completed(db_session, run.id, completed_at=1600, duration_ms=500)
    fetched = await get_run(db_session, run.id)
    assert fetched.status == "COMPLETED"
    assert fetched.duration_ms == 500


@pytest.mark.asyncio
async def test_mark_run_failed_stores_error_message(db_session):
    version = await get_or_create_default_strategy_version(db_session)
    run = await create_run(
        db_session,
        symbol="TESTUSDT",
        timeframe="1h",
        period_days=30,
        start_time=1000,
        end_time=2000,
        strategy_version_id=version.id,
        simulator_config=TradeSimulatorConfig(),
    )
    await mark_run_failed(db_session, run.id, "insufficient data", completed_at=1700, duration_ms=100)
    fetched = await get_run(db_session, run.id)
    assert fetched.status == "FAILED"
    assert fetched.error_message == "insufficient data"


@pytest.mark.asyncio
async def test_list_runs_filters_by_symbol_and_orders_newest_first(db_session):
    version = await get_or_create_default_strategy_version(db_session)
    for symbol in ("AAAUSDT", "BBBUSDT", "AAAUSDT"):
        await create_run(
            db_session,
            symbol=symbol,
            timeframe="1h",
            period_days=30,
            start_time=1000,
            end_time=2000,
            strategy_version_id=version.id,
            simulator_config=TradeSimulatorConfig(),
        )

    all_runs = await list_runs(db_session, limit=10)
    assert len(all_runs) == 3

    aaa_runs = await list_runs(db_session, symbol="AAAUSDT", limit=10)
    assert len(aaa_runs) == 2
    assert all(r.symbol == "AAAUSDT" for r in aaa_runs)


def _closed_trade(pnl: float) -> ClosedTrade:
    return ClosedTrade(
        symbol="TESTUSDT",
        direction="LONG",
        entry_time=0,
        entry_price=100.0,
        exit_time=3600,
        exit_price=100.0 + pnl,
        quantity=1.0,
        pnl=pnl,
        pnl_percent=pnl,
        exit_reason="TP1",
        duration_seconds=3600,
        decision_score=60.0,
        confidence=55.0,
        planned_risk_reward=1.5,
    )


@pytest.mark.asyncio
async def test_insert_and_get_trades(db_session):
    version = await get_or_create_default_strategy_version(db_session)
    run = await create_run(
        db_session,
        symbol="TESTUSDT",
        timeframe="1h",
        period_days=30,
        start_time=1000,
        end_time=2000,
        strategy_version_id=version.id,
        simulator_config=TradeSimulatorConfig(),
    )
    trades = [_closed_trade(10.0), _closed_trade(-5.0)]
    await insert_trades(db_session, run.id, trades)

    fetched = await get_trades(db_session, run.id, limit=10)
    assert len(fetched) == 2
    assert {t.pnl for t in fetched} == {10.0, -5.0}


@pytest.mark.asyncio
async def test_insert_and_get_metrics(db_session):
    version = await get_or_create_default_strategy_version(db_session)
    run = await create_run(
        db_session,
        symbol="TESTUSDT",
        timeframe="1h",
        period_days=30,
        start_time=1000,
        end_time=2000,
        strategy_version_id=version.id,
        simulator_config=TradeSimulatorConfig(),
    )
    performance = PerformanceMetrics(
        total_trades=2,
        winning_trades=1,
        losing_trades=1,
        total_return_percent=5.0,
        net_profit=50.0,
        gross_profit=60.0,
        gross_loss=-10.0,
        win_rate=50.0,
        loss_rate=50.0,
        avg_win=60.0,
        avg_loss=-10.0,
        profit_factor=6.0,
        expectancy=25.0,
        avg_trade_duration_seconds=3600.0,
    )
    risk = RiskMetrics(
        max_drawdown_percent=1.0,
        max_drawdown_duration_seconds=100,
        recovery_factor=50.0,
        sharpe_ratio=1.2,
        sortino_ratio=1.5,
        calmar_ratio=2.0,
        avg_risk_reward=1.5,
        final_balance=10_050.0,
        peak_balance=10_060.0,
    )
    await insert_metrics(db_session, run.id, performance, risk)

    fetched = await get_metrics(db_session, run.id)
    assert fetched is not None
    assert fetched.total_trades == 2
    assert fetched.sharpe_ratio == 1.2


@pytest.mark.asyncio
async def test_insert_and_get_equity_curve(db_session):
    version = await get_or_create_default_strategy_version(db_session)
    run = await create_run(
        db_session,
        symbol="TESTUSDT",
        timeframe="1h",
        period_days=30,
        start_time=1000,
        end_time=2000,
        strategy_version_id=version.id,
        simulator_config=TradeSimulatorConfig(),
    )
    points = [
        EquityPoint(time=1000, balance=10_000.0, drawdown_percent=0.0, cumulative_pnl=0.0, trade_count=0),
        EquityPoint(time=2000, balance=10_050.0, drawdown_percent=0.0, cumulative_pnl=50.0, trade_count=1),
    ]
    await insert_equity_curve(db_session, run.id, points)

    fetched = await get_equity_curve(db_session, run.id)
    assert len(fetched) == 2
    assert fetched[0].time == 1000
    assert fetched[1].balance == 10_050.0
