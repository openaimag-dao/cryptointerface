"""Backtesting Engine API — see app/backtesting/. `/run` executes
synchronously and returns the full report immediately (a run is bounded
to `MAX_BACKTEST_BARS` bars precisely so this never turns into a
long-hanging request — see app/backtesting/utils/timeframes.py).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.backtesting.engine import run_backtest
from app.backtesting.models.config import BacktestConfig, TradeSimulatorConfig
from app.backtesting.utils.errors import InsufficientDataError, InvalidParametersError
from app.database.session import get_db
from app.models.backtest_metrics import BacktestMetrics
from app.models.backtest_run import BacktestRun
from app.models.backtest_trade import BacktestTrade
from app.models.equity_curve import EquityCurvePoint
from app.schemas.backtest import (
    BacktestMetricsOut,
    BacktestReportOut,
    BacktestRunOut,
    BacktestRunRequest,
    BacktestTradeOut,
    EquityPointOut,
    PerformanceMetricsOut,
    RiskMetricsOut,
)
from app.services.backtest_repository import (
    get_equity_curve,
    get_metrics,
    get_run,
    get_strategy_version,
    get_trades,
    list_runs,
)

router = APIRouter(prefix="/api/backtesting", tags=["backtesting"])


async def _run_out(db: AsyncSession, run: BacktestRun) -> BacktestRunOut:
    version = await get_strategy_version(db, run.strategy_version_id)
    return BacktestRunOut(
        id=str(run.id),
        symbol=run.symbol,
        timeframe=run.timeframe,
        period_days=run.period_days,
        start_time=run.start_time,
        end_time=run.end_time,
        status=run.status,
        strategy_version_name=version.name if version else "unknown",
        initial_balance=run.initial_balance,
        commission_bps=run.commission_bps,
        slippage_bps=run.slippage_bps,
        error_message=run.error_message,
        started_at=run.started_at,
        completed_at=run.completed_at,
        duration_ms=run.duration_ms,
    )


def _performance_out(metrics: BacktestMetrics) -> PerformanceMetricsOut:
    return PerformanceMetricsOut(
        total_trades=metrics.total_trades,
        winning_trades=metrics.winning_trades,
        losing_trades=metrics.losing_trades,
        total_return_percent=metrics.total_return_percent,
        net_profit=metrics.net_profit,
        gross_profit=metrics.gross_profit,
        gross_loss=metrics.gross_loss,
        win_rate=metrics.win_rate,
        loss_rate=metrics.loss_rate,
        avg_win=metrics.avg_win,
        avg_loss=metrics.avg_loss,
        profit_factor=metrics.profit_factor,
        expectancy=metrics.expectancy,
        avg_trade_duration_seconds=metrics.avg_trade_duration_seconds,
    )


def _risk_out(metrics: BacktestMetrics) -> RiskMetricsOut:
    return RiskMetricsOut(
        max_drawdown_percent=metrics.max_drawdown_percent,
        max_drawdown_duration_seconds=metrics.max_drawdown_duration_seconds,
        recovery_factor=metrics.recovery_factor,
        sharpe_ratio=metrics.sharpe_ratio,
        sortino_ratio=metrics.sortino_ratio,
        calmar_ratio=metrics.calmar_ratio,
        avg_risk_reward=metrics.avg_risk_reward,
        final_balance=metrics.final_balance,
        peak_balance=metrics.peak_balance,
    )


def _trade_out(trade: BacktestTrade) -> BacktestTradeOut:
    return BacktestTradeOut(
        id=str(trade.id),
        symbol=trade.symbol,
        direction=trade.direction,
        entry_time=trade.entry_time,
        entry_price=trade.entry_price,
        exit_time=trade.exit_time,
        exit_price=trade.exit_price,
        quantity=trade.quantity,
        pnl=trade.pnl,
        pnl_percent=trade.pnl_percent,
        exit_reason=trade.exit_reason,
        duration_seconds=trade.duration_seconds,
        decision_score=trade.decision_score,
        confidence=trade.confidence,
        planned_risk_reward=trade.planned_risk_reward,
    )


def _equity_point_out(point: EquityCurvePoint) -> EquityPointOut:
    return EquityPointOut(
        time=point.time,
        balance=point.balance,
        drawdown_percent=point.drawdown_percent,
        cumulative_pnl=point.cumulative_pnl,
        trade_count=point.trade_count,
    )


async def _get_run_or_404(db: AsyncSession, run_id: int) -> BacktestRun:
    run = await get_run(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"No backtest run with id {run_id}")
    return run


@router.post("/run", response_model=BacktestReportOut)
async def run(request: BacktestRunRequest, db: AsyncSession = Depends(get_db)) -> BacktestReportOut:
    config = BacktestConfig(
        symbol=request.symbol.upper(),
        timeframe=request.timeframe,
        period_days=request.period_days,
        strategy_version_name="v1-default-decision-engine",
        simulator=TradeSimulatorConfig(
            initial_balance=request.initial_balance,
            commission_bps=request.commission_bps,
            slippage_bps=request.slippage_bps,
            risk_per_trade_percent=request.risk_per_trade_percent,
        ),
    )

    try:
        run_id, _ = await run_backtest(db, config)
    except InvalidParametersError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except InsufficientDataError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    run_row = await _get_run_or_404(db, run_id)
    metrics = await get_metrics(db, run_id)
    if metrics is None:
        raise HTTPException(status_code=500, detail="Backtest completed but metrics were not persisted")

    run_out = await _run_out(db, run_row)
    return BacktestReportOut(run=run_out, performance=_performance_out(metrics), risk=_risk_out(metrics))


@router.get("/history", response_model=list[BacktestRunOut])
async def history(
    symbol: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[BacktestRunOut]:
    runs = await list_runs(db, symbol=symbol.upper() if symbol else None, limit=limit, offset=offset)
    return [await _run_out(db, run_row) for run_row in runs]


@router.get("/report/{run_id}", response_model=BacktestReportOut)
async def report(run_id: int, db: AsyncSession = Depends(get_db)) -> BacktestReportOut:
    run_row = await _get_run_or_404(db, run_id)
    metrics = await get_metrics(db, run_id)
    if metrics is None:
        raise HTTPException(
            status_code=409, detail=f"Run {run_id} has status {run_row.status} — metrics aren't available yet"
        )
    run_out = await _run_out(db, run_row)
    return BacktestReportOut(run=run_out, performance=_performance_out(metrics), risk=_risk_out(metrics))


@router.get("/metrics/{run_id}", response_model=BacktestMetricsOut)
async def metrics(run_id: int, db: AsyncSession = Depends(get_db)) -> BacktestMetricsOut:
    run_row = await _get_run_or_404(db, run_id)
    metrics_row = await get_metrics(db, run_id)
    if metrics_row is None:
        raise HTTPException(
            status_code=409, detail=f"Run {run_id} has status {run_row.status} — metrics aren't available yet"
        )
    return BacktestMetricsOut(performance=_performance_out(metrics_row), risk=_risk_out(metrics_row))


@router.get("/trades/{run_id}", response_model=list[BacktestTradeOut])
async def trades(
    run_id: int,
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[BacktestTradeOut]:
    await _get_run_or_404(db, run_id)
    rows = await get_trades(db, run_id, limit=limit, offset=offset)
    return [_trade_out(row) for row in rows]


@router.get("/equity/{run_id}", response_model=list[EquityPointOut])
async def equity(run_id: int, db: AsyncSession = Depends(get_db)) -> list[EquityPointOut]:
    await _get_run_or_404(db, run_id)
    points = await get_equity_curve(db, run_id)
    return [_equity_point_out(point) for point in points]
