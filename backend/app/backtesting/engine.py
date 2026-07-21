"""Backtesting Engine — orchestrates one full run: validates parameters,
bulk-loads history, replays the Decision Engine bar by bar
(`strategy_runner.py`), simulates fills (`trade_simulator.py`), computes
metrics (`performance.py` + `risk_metrics.py`), and persists everything
(`app/services/backtest_repository.py`).

Logging covers exactly what the Sprint 5 spec asks for: start, end,
errors, and execution time (`backtest_started`/`backtest_completed`/
`backtest_failed`, all carrying `duration_ms`).
"""

import time
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_engine.market_context import DEFAULT_CANDLE_LOOKBACK, DEFAULT_FUNDING_LOOKBACK, DEFAULT_OI_LOOKBACK
from app.backtesting.models.config import BacktestConfig
from app.backtesting.models.results import BacktestRunResult, EquityPoint
from app.backtesting.models.trade import ClosedTrade
from app.backtesting.performance import compute_performance_metrics
from app.backtesting.risk_metrics import compute_risk_metrics
from app.backtesting.strategy_runner import iter_decisions
from app.backtesting.trade_simulator import TradeSimulator
from app.backtesting.utils.errors import BacktestError, ComputationError, InsufficientDataError
from app.backtesting.utils.timeframes import period_to_bar_count, validate_backtest_params
from app.core.logging import get_logger
from app.services.backtest_repository import (
    create_run,
    get_or_create_default_strategy_version,
    insert_equity_curve,
    insert_metrics,
    insert_trades,
    mark_run_completed,
    mark_run_failed,
    mark_run_running,
)
from app.services.market_repository import (
    get_candle_time_bounds,
    get_recent_candles,
    get_recent_funding_history,
    get_recent_open_interest_history,
    to_candle_schema,
)

logger = get_logger(__name__)

# Generous, bounded caps for the funding/OI bulk fetch — both series are
# far sparser than candles (funding every 8h, OI on its own poll
# interval), so even a year's worth comfortably fits under these without
# risking an unbounded query.
FUNDING_FETCH_LIMIT = 5_000
OI_FETCH_LIMIT = 50_000


def _now() -> int:
    return int(datetime.now(UTC).timestamp())


def _build_equity_curve(trades: list[ClosedTrade], initial_balance: float, start_time: int) -> list[EquityPoint]:
    """One point per trade close, plus a leading point at the run's
    start — see `EquityCurvePoint`'s docstring for why this is the exact
    curve, not a downsampled approximation."""
    points = [
        EquityPoint(time=start_time, balance=initial_balance, drawdown_percent=0.0, cumulative_pnl=0.0, trade_count=0)
    ]
    balance = initial_balance
    peak = initial_balance
    cumulative_pnl = 0.0
    for i, trade in enumerate(trades, start=1):
        balance += trade.pnl
        cumulative_pnl += trade.pnl
        peak = max(peak, balance)
        drawdown_pct = ((peak - balance) / peak * 100.0) if peak > 0 else 0.0
        points.append(
            EquityPoint(
                time=trade.exit_time,
                balance=balance,
                drawdown_percent=drawdown_pct,
                cumulative_pnl=cumulative_pnl,
                trade_count=i,
            )
        )
    return points


async def run_backtest(db: AsyncSession, config: BacktestConfig) -> tuple[int, BacktestRunResult]:
    """Runs one backtest end to end and persists it. Returns
    `(backtest_run_id, result)`. Raises `BacktestError` subclasses for
    every failure mode the spec calls out (insufficient data, invalid
    parameters); anything else is wrapped in `ComputationError` so the
    caller never has to distinguish "a bug" from "a known failure mode"
    to decide what to tell the user — both come back as a clean FAILED
    run with a message, never a raw traceback.
    """
    validate_backtest_params(config.symbol, config.timeframe, config.period_days)

    strategy_version = await get_or_create_default_strategy_version(db)
    bar_count = period_to_bar_count(config.period_days, config.timeframe)
    total_needed = DEFAULT_CANDLE_LOOKBACK + bar_count

    bounds = await get_candle_time_bounds(db, config.symbol, config.timeframe)
    if bounds is None:
        raise InsufficientDataError(
            f"No historical candles on file for {config.symbol}/{config.timeframe}. "
            "The Data Engine needs to backfill this symbol/timeframe before it can be backtested."
        )
    _, latest = bounds

    run = await create_run(
        db,
        symbol=config.symbol,
        timeframe=config.timeframe,
        period_days=config.period_days,
        start_time=latest,  # placeholder, corrected below once the real window is known
        end_time=latest,
        strategy_version_id=strategy_version.id,
        simulator_config=config.simulator,
    )

    start_perf = time.monotonic()
    started_at = _now()
    await mark_run_running(db, run.id, started_at)
    logger.info(
        "backtest_started",
        extra={
            "run_id": run.id,
            "symbol": config.symbol,
            "timeframe": config.timeframe,
            "period_days": config.period_days,
        },
    )

    try:
        candle_rows = await get_recent_candles(db, config.symbol, config.timeframe, limit=total_needed, as_of=latest)
        if len(candle_rows) < DEFAULT_CANDLE_LOOKBACK + 1:
            raise InsufficientDataError(
                f"{config.symbol}/{config.timeframe} only has {len(candle_rows)} candles on file — "
                f"need at least {DEFAULT_CANDLE_LOOKBACK + 1} (warm-up + 1 bar to analyze). "
                "Wait for more history to backfill or pick a lower-timeframe symbol with deeper history."
            )
        if len(candle_rows) < total_needed:
            raise InsufficientDataError(
                f"Requested {config.period_days} days of {config.timeframe} candles for {config.symbol} "
                f"needs {total_needed} candles (including {DEFAULT_CANDLE_LOOKBACK} bars of warm-up); "
                f"only {len(candle_rows)} are on file. Try a shorter period or wait for more history to backfill."
            )

        candles = [to_candle_schema(row) for row in candle_rows]
        funding_history = await get_recent_funding_history(db, config.symbol, limit=FUNDING_FETCH_LIMIT, as_of=latest)
        oi_history = await get_recent_open_interest_history(db, config.symbol, limit=OI_FETCH_LIMIT, as_of=latest)

        simulator = TradeSimulator(config.simulator)
        total_bars = len(candles)
        bars_analyzed = 0
        for idx, bar_decision in enumerate(
            iter_decisions(
                config.symbol,
                config.timeframe,
                candles,
                funding_history,
                oi_history,
                candle_lookback=DEFAULT_CANDLE_LOOKBACK,
                funding_lookback=DEFAULT_FUNDING_LOOKBACK,
                oi_lookback=DEFAULT_OI_LOOKBACK,
            )
        ):
            is_last = idx == total_bars - 1
            simulator.process_bar(config.symbol, bar_decision.bar, bar_decision.decision, is_last)
            if bar_decision.decision is not None:
                bars_analyzed += 1

        trades = simulator.closed_trades
        actual_start_time = candles[DEFAULT_CANDLE_LOOKBACK - 1].time
        actual_end_time = candles[-1].time

        performance = compute_performance_metrics(trades, config.simulator.initial_balance)
        risk = compute_risk_metrics(trades, config.simulator.initial_balance, config.period_days)
        equity_curve = _build_equity_curve(trades, config.simulator.initial_balance, actual_start_time)

        result = BacktestRunResult(
            symbol=config.symbol,
            timeframe=config.timeframe,
            period_days=config.period_days,
            start_time=actual_start_time,
            end_time=actual_end_time,
            strategy_version_name=strategy_version.name,
            trades=trades,
            equity_curve=equity_curve,
            performance=performance,
            risk=risk,
            bars_analyzed=bars_analyzed,
        )

        await insert_trades(db, run.id, trades)
        await insert_metrics(db, run.id, performance, risk)
        await insert_equity_curve(db, run.id, equity_curve)

        run.start_time = actual_start_time
        run.end_time = actual_end_time
        await db.commit()

        duration_ms = int((time.monotonic() - start_perf) * 1000)
        await mark_run_completed(db, run.id, _now(), duration_ms)
        logger.info(
            "backtest_completed",
            extra={
                "run_id": run.id,
                "symbol": config.symbol,
                "bars_analyzed": bars_analyzed,
                "total_trades": performance.total_trades,
                "duration_ms": duration_ms,
            },
        )
        return run.id, result

    except BacktestError as exc:
        duration_ms = int((time.monotonic() - start_perf) * 1000)
        await mark_run_failed(db, run.id, str(exc), _now(), duration_ms)
        logger.warning("backtest_failed", extra={"run_id": run.id, "error": str(exc), "duration_ms": duration_ms})
        raise
    except Exception as exc:  # noqa: BLE001 — always fail the run cleanly before re-raising
        duration_ms = int((time.monotonic() - start_perf) * 1000)
        wrapped = ComputationError(f"Unexpected error computing backtest: {exc}")
        await mark_run_failed(db, run.id, str(wrapped), _now(), duration_ms)
        logger.error(
            "backtest_failed", extra={"run_id": run.id, "error": str(exc), "duration_ms": duration_ms}, exc_info=True
        )
        raise wrapped from exc
