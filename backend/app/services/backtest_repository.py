"""Persistence for the Backtesting Engine (`app/backtesting/`) — the five
Sprint 5 tables: `strategy_versions`, `backtest_runs`, `backtest_trades`,
`backtest_metrics`, `equity_curve`.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_engine.decision_engine import MIN_CONFIDENCE_FOR_ACTION
from app.ai_engine.market_score import FACTOR_WEIGHTS
from app.ai_engine.risk_engine import ATR_PERIOD, STOP_ATR_MULTIPLIER, TP1_R_MULTIPLE, TP2_R_MULTIPLE, TP3_R_MULTIPLE
from app.backtesting.models.config import TradeSimulatorConfig
from app.backtesting.models.results import EquityPoint, PerformanceMetrics, RiskMetrics
from app.backtesting.models.trade import ClosedTrade
from app.models.backtest_metrics import BacktestMetrics
from app.models.backtest_run import BacktestRun
from app.models.backtest_trade import BacktestTrade
from app.models.equity_curve import EquityCurvePoint
from app.models.strategy_version import StrategyVersion

DEFAULT_STRATEGY_VERSION_NAME = "v1-default-decision-engine"


def _default_strategy_config() -> dict:
    """A JSON audit snapshot of the Sprint 3 Decision Engine's tunable
    constants — record-keeping only, see `StrategyVersion`'s docstring."""
    return {
        "min_confidence_for_action": MIN_CONFIDENCE_FOR_ACTION,
        "factor_weights": dict(FACTOR_WEIGHTS),
        "atr_period": ATR_PERIOD,
        "stop_atr_multiplier": STOP_ATR_MULTIPLIER,
        "tp_r_multiples": [TP1_R_MULTIPLE, TP2_R_MULTIPLE, TP3_R_MULTIPLE],
    }


async def get_or_create_default_strategy_version(db: AsyncSession) -> StrategyVersion:
    stmt = select(StrategyVersion).where(StrategyVersion.name == DEFAULT_STRATEGY_VERSION_NAME)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing

    version = StrategyVersion(
        name=DEFAULT_STRATEGY_VERSION_NAME,
        description=(
            "The unmodified Sprint 3 AI Decision Engine (app/ai_engine/decision_engine.py), "
            "replayed bar by bar with no look-ahead. See app/backtesting/strategy_runner.py."
        ),
        config=_default_strategy_config(),
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)
    return version


async def get_strategy_version(db: AsyncSession, strategy_version_id: int) -> StrategyVersion | None:
    return await db.get(StrategyVersion, strategy_version_id)


async def list_strategy_versions(db: AsyncSession) -> list[StrategyVersion]:
    result = await db.execute(select(StrategyVersion).order_by(StrategyVersion.created_at.asc()))
    return list(result.scalars().all())


async def create_run(
    db: AsyncSession,
    *,
    symbol: str,
    timeframe: str,
    period_days: int,
    start_time: int,
    end_time: int,
    strategy_version_id: int,
    simulator_config: TradeSimulatorConfig,
) -> BacktestRun:
    run = BacktestRun(
        symbol=symbol,
        timeframe=timeframe,
        period_days=period_days,
        start_time=start_time,
        end_time=end_time,
        strategy_version_id=strategy_version_id,
        status="PENDING",
        initial_balance=simulator_config.initial_balance,
        commission_bps=simulator_config.commission_bps,
        slippage_bps=simulator_config.slippage_bps,
        config={
            "risk_per_trade_percent": simulator_config.risk_per_trade_percent,
            "allow_concurrent_positions": simulator_config.allow_concurrent_positions,
            "trailing_stop_enabled": simulator_config.trailing_stop_enabled,
            "trailing_stop_atr_multiplier": simulator_config.trailing_stop_atr_multiplier,
            "break_even_enabled": simulator_config.break_even_enabled,
            "break_even_trigger_r": simulator_config.break_even_trigger_r,
            "partial_take_profit_enabled": simulator_config.partial_take_profit_enabled,
            "partial_take_profit_levels": list(simulator_config.partial_take_profit_levels),
        },
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


async def mark_run_running(db: AsyncSession, run_id: int, started_at: int) -> None:
    run = await db.get(BacktestRun, run_id)
    if run is None:
        return
    run.status = "RUNNING"
    run.started_at = started_at
    await db.commit()


async def mark_run_completed(db: AsyncSession, run_id: int, completed_at: int, duration_ms: int) -> None:
    run = await db.get(BacktestRun, run_id)
    if run is None:
        return
    run.status = "COMPLETED"
    run.completed_at = completed_at
    run.duration_ms = duration_ms
    await db.commit()


async def mark_run_failed(
    db: AsyncSession, run_id: int, error_message: str, completed_at: int, duration_ms: int
) -> None:
    run = await db.get(BacktestRun, run_id)
    if run is None:
        return
    run.status = "FAILED"
    run.error_message = error_message[:2000]
    run.completed_at = completed_at
    run.duration_ms = duration_ms
    await db.commit()


async def insert_trades(db: AsyncSession, run_id: int, trades: list[ClosedTrade]) -> None:
    if not trades:
        return
    rows = [
        BacktestTrade(
            backtest_run_id=run_id,
            symbol=t.symbol,
            direction=t.direction,
            entry_time=t.entry_time,
            entry_price=t.entry_price,
            exit_time=t.exit_time,
            exit_price=t.exit_price,
            quantity=t.quantity,
            pnl=t.pnl,
            pnl_percent=t.pnl_percent,
            exit_reason=t.exit_reason,
            duration_seconds=t.duration_seconds,
            decision_score=t.decision_score,
            confidence=t.confidence,
            planned_risk_reward=t.planned_risk_reward,
        )
        for t in trades
    ]
    db.add_all(rows)
    await db.commit()


async def insert_metrics(db: AsyncSession, run_id: int, performance: PerformanceMetrics, risk: RiskMetrics) -> None:
    db.add(
        BacktestMetrics(
            backtest_run_id=run_id,
            total_trades=performance.total_trades,
            winning_trades=performance.winning_trades,
            losing_trades=performance.losing_trades,
            total_return_percent=performance.total_return_percent,
            net_profit=performance.net_profit,
            gross_profit=performance.gross_profit,
            gross_loss=performance.gross_loss,
            win_rate=performance.win_rate,
            loss_rate=performance.loss_rate,
            avg_win=performance.avg_win,
            avg_loss=performance.avg_loss,
            profit_factor=performance.profit_factor,
            expectancy=performance.expectancy,
            avg_trade_duration_seconds=performance.avg_trade_duration_seconds,
            max_drawdown_percent=risk.max_drawdown_percent,
            recovery_factor=risk.recovery_factor,
            sharpe_ratio=risk.sharpe_ratio,
            sortino_ratio=risk.sortino_ratio,
            calmar_ratio=risk.calmar_ratio,
            avg_risk_reward=risk.avg_risk_reward,
            final_balance=risk.final_balance,
            peak_balance=risk.peak_balance,
            max_drawdown_duration_seconds=risk.max_drawdown_duration_seconds,
        )
    )
    await db.commit()


async def insert_equity_curve(db: AsyncSession, run_id: int, points: list[EquityPoint]) -> None:
    if not points:
        return
    rows = [
        EquityCurvePoint(
            backtest_run_id=run_id,
            time=p.time,
            balance=p.balance,
            drawdown_percent=p.drawdown_percent,
            cumulative_pnl=p.cumulative_pnl,
            trade_count=p.trade_count,
        )
        for p in points
    ]
    db.add_all(rows)
    await db.commit()


async def get_run(db: AsyncSession, run_id: int) -> BacktestRun | None:
    return await db.get(BacktestRun, run_id)


async def list_runs(db: AsyncSession, symbol: str | None = None, limit: int = 20, offset: int = 0) -> list[BacktestRun]:
    stmt = select(BacktestRun)
    if symbol is not None:
        stmt = stmt.where(BacktestRun.symbol == symbol)
    stmt = stmt.order_by(BacktestRun.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_metrics(db: AsyncSession, run_id: int) -> BacktestMetrics | None:
    stmt = select(BacktestMetrics).where(BacktestMetrics.backtest_run_id == run_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_trades(db: AsyncSession, run_id: int, limit: int = 200, offset: int = 0) -> list[BacktestTrade]:
    stmt = (
        select(BacktestTrade)
        .where(BacktestTrade.backtest_run_id == run_id)
        .order_by(BacktestTrade.entry_time.asc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_equity_curve(db: AsyncSession, run_id: int) -> list[EquityCurvePoint]:
    stmt = (
        select(EquityCurvePoint).where(EquityCurvePoint.backtest_run_id == run_id).order_by(EquityCurvePoint.time.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
