"""Walk-Forward Testing — architecture for Train / Validation / Forward
Test splits (Sprint 5 spec). Basic scenario only, as the spec asks for:
this module slices historical data into sequential Train/Validation/Test
folds and runs the (unmodified) Decision Engine over each fold's Test
segment — it does **not** yet fit or tune any parameter on the Train/
Validation segments, because there is nothing to tune yet (`optimizer.py`
is interface-only). Train/Validation windows are reported for every fold
so the shape is in place for when the Optimizer is real: at that point,
each fold would fit parameters on Train, pick/confirm them on Validation,
and only then measure out-of-sample performance on Test — exactly what
this module's fold boundaries already describe.

Reuses the exact same primitives `engine.py` does
(`strategy_runner.iter_decisions` + `TradeSimulator` +
`performance.py`/`risk_metrics.py`) rather than duplicating them, so a
walk-forward fold's Test segment is scored identically to a standalone
backtest over the same bars. Not persisted to the database — the Sprint 5
spec's five tables don't include one for walk-forward folds, and each
fold's result is cheap to recompute on demand.
"""

from dataclasses import dataclass, field

from app.ai_engine.market_context import DEFAULT_CANDLE_LOOKBACK, DEFAULT_FUNDING_LOOKBACK, DEFAULT_OI_LOOKBACK
from app.backtesting.models.config import TradeSimulatorConfig
from app.backtesting.models.results import BacktestRunResult, EquityPoint
from app.backtesting.performance import compute_performance_metrics
from app.backtesting.risk_metrics import compute_risk_metrics
from app.backtesting.strategy_runner import iter_decisions
from app.backtesting.trade_simulator import TradeSimulator
from app.backtesting.utils.errors import InsufficientDataError, InvalidParametersError
from app.backtesting.utils.timeframes import period_to_bar_count, validate_symbol_and_timeframe
from app.models.funding import FundingRate
from app.models.open_interest import OpenInterest
from app.schemas.candle import Candle


@dataclass(frozen=True)
class WalkForwardConfig:
    symbol: str
    timeframe: str
    train_days: int
    validation_days: int
    test_days: int
    folds: int = 3
    simulator: TradeSimulatorConfig = field(default_factory=TradeSimulatorConfig)


@dataclass(frozen=True)
class WalkForwardFold:
    fold_index: int
    train_start: int
    train_end: int
    validation_start: int
    validation_end: int
    test_start: int
    test_end: int
    test_result: BacktestRunResult


@dataclass(frozen=True)
class WalkForwardResult:
    symbol: str
    timeframe: str
    folds: list[WalkForwardFold]


def _run_segment(
    symbol: str,
    timeframe: str,
    warmup: list[Candle],
    segment: list[Candle],
    funding_history: list[FundingRate],
    oi_history: list[OpenInterest],
    simulator_config: TradeSimulatorConfig,
) -> BacktestRunResult:
    """Runs the Decision Engine + Trade Simulator over `segment`, using
    `warmup` (bars strictly before `segment`) for indicator context —
    same "fixed lookback window, nothing from after the bar being
    decided" guarantee as `engine.py`, just without a database round-trip
    since the caller already has everything in memory."""
    candles = warmup + segment
    simulator = TradeSimulator(simulator_config)
    total = len(candles)
    for idx, bar_decision in enumerate(
        iter_decisions(
            symbol,
            timeframe,
            candles,
            funding_history,
            oi_history,
            candle_lookback=DEFAULT_CANDLE_LOOKBACK,
            funding_lookback=DEFAULT_FUNDING_LOOKBACK,
            oi_lookback=DEFAULT_OI_LOOKBACK,
        )
    ):
        if idx < len(warmup):
            continue  # never open/monitor trades during the warm-up prefix itself
        simulator.process_bar(symbol, bar_decision.bar, bar_decision.decision, idx == total - 1)

    trades = simulator.closed_trades
    performance = compute_performance_metrics(trades, simulator_config.initial_balance)
    period_days = max(1, (segment[-1].time - segment[0].time) // 86_400)
    risk = compute_risk_metrics(trades, simulator_config.initial_balance, period_days)

    points = [
        EquityPoint(
            time=segment[0].time,
            balance=simulator_config.initial_balance,
            drawdown_percent=0.0,
            cumulative_pnl=0.0,
            trade_count=0,
        )
    ]
    balance = simulator_config.initial_balance
    peak = balance
    cumulative = 0.0
    for i, trade in enumerate(trades, start=1):
        balance += trade.pnl
        cumulative += trade.pnl
        peak = max(peak, balance)
        drawdown = ((peak - balance) / peak * 100.0) if peak > 0 else 0.0
        points.append(
            EquityPoint(
                time=trade.exit_time,
                balance=balance,
                drawdown_percent=drawdown,
                cumulative_pnl=cumulative,
                trade_count=i,
            )
        )

    return BacktestRunResult(
        symbol=symbol,
        timeframe=timeframe,
        period_days=period_days,
        start_time=segment[0].time,
        end_time=segment[-1].time,
        strategy_version_name="v1-default-decision-engine",
        trades=trades,
        equity_curve=points,
        performance=performance,
        risk=risk,
        bars_analyzed=len(segment),
    )


def run_walk_forward(
    config: WalkForwardConfig,
    candles: list[Candle],
    funding_history: list[FundingRate],
    oi_history: list[OpenInterest],
) -> WalkForwardResult:
    """`candles` must already be the full ascending history the caller
    wants to walk forward over (bulk-fetched once, same as `engine.py`).
    Folds are non-overlapping and move forward in time: fold N's Train
    window starts immediately after fold N-1's Test window ends.
    """
    validate_symbol_and_timeframe(config.symbol, config.timeframe)

    if config.train_days <= 0 or config.validation_days <= 0 or config.test_days <= 0:
        raise InvalidParametersError("train_days, validation_days, and test_days must all be positive")
    if config.folds <= 0:
        raise InvalidParametersError("folds must be positive")

    train_bars = period_to_bar_count(config.train_days, config.timeframe)
    validation_bars = period_to_bar_count(config.validation_days, config.timeframe)
    test_bars = period_to_bar_count(config.test_days, config.timeframe)
    fold_bars = train_bars + validation_bars + test_bars
    if fold_bars <= 0:
        raise InvalidParametersError("train_days, validation_days, and test_days must combine to at least one bar")

    total_needed = DEFAULT_CANDLE_LOOKBACK + fold_bars * config.folds
    if len(candles) < total_needed:
        raise InsufficientDataError(
            f"Walk-forward over {config.folds} folds of {config.train_days}/{config.validation_days}/"
            f"{config.test_days} (train/validation/test) days needs {total_needed} {config.timeframe} "
            f"candles; only {len(candles)} are on file."
        )

    # Use the most recent data: the last `total_needed` candles, folds
    # laid out oldest-first so fold 0 is the earliest, most out-of-sample-
    # distant fold and the last fold ends at the most recent bar. Every
    # slice below is taken from this single flat, chronologically
    # continuous list by absolute position — never reassembled from
    # separately-sliced pieces — so there's no risk of silently splicing
    # together two non-adjacent time ranges (which would corrupt the
    # sliding-window indicators computed across the join).
    window = candles[-total_needed:]

    folds: list[WalkForwardFold] = []
    for fold_index in range(config.folds):
        fold_start = DEFAULT_CANDLE_LOOKBACK + fold_index * fold_bars
        train_slice = window[fold_start : fold_start + train_bars]
        validation_slice = window[fold_start + train_bars : fold_start + train_bars + validation_bars]
        test_start = fold_start + train_bars + validation_bars
        test_slice = window[test_start : test_start + test_bars]
        # The DEFAULT_CANDLE_LOOKBACK bars immediately preceding the Test
        # segment, wherever they actually fall (this fold's own Train/
        # Validation, a prior fold, or the shared prefix) — always the
        # real, contiguous history, so indicators warm up correctly.
        test_warmup = window[test_start - DEFAULT_CANDLE_LOOKBACK : test_start]

        test_result = _run_segment(
            config.symbol, config.timeframe, test_warmup, test_slice, funding_history, oi_history, config.simulator
        )

        folds.append(
            WalkForwardFold(
                fold_index=fold_index,
                train_start=train_slice[0].time,
                train_end=train_slice[-1].time,
                validation_start=validation_slice[0].time,
                validation_end=validation_slice[-1].time,
                test_start=test_slice[0].time,
                test_end=test_slice[-1].time,
                test_result=test_result,
            )
        )

    return WalkForwardResult(symbol=config.symbol, timeframe=config.timeframe, folds=folds)
