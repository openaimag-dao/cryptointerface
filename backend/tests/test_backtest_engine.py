import numpy as np
import pytest

from app.backtesting.engine import run_backtest
from app.backtesting.models.config import BacktestConfig, TradeSimulatorConfig
from app.backtesting.utils.errors import InsufficientDataError, InvalidParametersError
from app.services.backtest_repository import get_run, list_runs
from app.services.binance.rest_client import KlineData
from app.services.market_repository import bulk_upsert_candles


async def _seed_candles(db_session, symbol: str, n: int, start_time_ms: int = 1_680_000_000_000) -> None:
    closes = 100 + np.cumsum(np.sin(np.linspace(0, 40, n)) * 0.5 + np.random.RandomState(1).normal(0, 0.2, n))
    klines = []
    for i in range(n):
        open_time = start_time_ms + i * 3_600_000
        close = float(closes[i])
        open_ = float(closes[i - 1]) if i > 0 else close
        high = max(open_, close) + 0.3
        low = min(open_, close) - 0.3
        klines.append(
            KlineData(
                open_time=open_time,
                close_time=open_time + 3_599_999,
                open=open_,
                high=high,
                low=low,
                close=close,
                volume=1_000.0 + i,
                quote_volume=100_000.0,
                trades=100,
            )
        )
    await bulk_upsert_candles(db_session, symbol, "1h", klines)


@pytest.mark.asyncio
async def test_run_backtest_raises_invalid_parameters_without_creating_a_run(db_session):
    config = BacktestConfig(
        symbol="TESTUSDT", timeframe="1h", period_days=45, strategy_version_name="v1-default-decision-engine"
    )
    with pytest.raises(InvalidParametersError):
        await run_backtest(db_session, config)

    runs = await list_runs(db_session, limit=10)
    assert runs == []


@pytest.mark.asyncio
async def test_run_backtest_raises_insufficient_data_and_marks_run_failed(db_session):
    await _seed_candles(db_session, "THINUSDT", n=50)
    config = BacktestConfig(
        symbol="THINUSDT", timeframe="1h", period_days=30, strategy_version_name="v1-default-decision-engine"
    )
    with pytest.raises(InsufficientDataError):
        await run_backtest(db_session, config)

    runs = await list_runs(db_session, symbol="THINUSDT", limit=10)
    assert len(runs) == 1
    assert runs[0].status == "FAILED"
    assert runs[0].error_message is not None


@pytest.mark.asyncio
async def test_run_backtest_no_data_at_all_raises_insufficient_data(db_session):
    config = BacktestConfig(
        symbol="NODATAUSDT", timeframe="1h", period_days=30, strategy_version_name="v1-default-decision-engine"
    )
    with pytest.raises(InsufficientDataError):
        await run_backtest(db_session, config)


@pytest.mark.asyncio
async def test_run_backtest_success_persists_everything(db_session):
    await _seed_candles(db_session, "TESTUSDT", n=1_000)
    config = BacktestConfig(
        symbol="TESTUSDT",
        timeframe="1h",
        period_days=30,
        strategy_version_name="v1-default-decision-engine",
        simulator=TradeSimulatorConfig(initial_balance=10_000.0),
    )

    run_id, result = await run_backtest(db_session, config)

    assert result.bars_analyzed > 0
    assert result.performance.total_trades == len(result.trades)
    assert result.risk.final_balance == result.equity_curve[-1].balance

    run_row = await get_run(db_session, run_id)
    assert run_row.status == "COMPLETED"
    assert run_row.duration_ms is not None
    assert run_row.completed_at is not None


@pytest.mark.asyncio
async def test_run_backtest_deterministic_same_input_same_output(db_session):
    await _seed_candles(db_session, "TESTUSDT", n=1_000)
    config = BacktestConfig(
        symbol="TESTUSDT", timeframe="1h", period_days=30, strategy_version_name="v1-default-decision-engine"
    )

    _, first = await run_backtest(db_session, config)
    _, second = await run_backtest(db_session, config)

    assert first.performance.total_trades == second.performance.total_trades
    assert first.performance.net_profit == second.performance.net_profit
    assert first.risk.max_drawdown_percent == second.risk.max_drawdown_percent
    assert len(first.trades) == len(second.trades)
    for a, b in zip(first.trades, second.trades, strict=True):
        assert a.entry_time == b.entry_time
        assert a.pnl == b.pnl
