import numpy as np
import pytest

from app.backtesting.models.config import TradeSimulatorConfig
from app.backtesting.utils.errors import InsufficientDataError, InvalidParametersError
from app.backtesting.walk_forward import WalkForwardConfig, run_walk_forward
from app.schemas.candle import Candle


def _candles(n: int, start_time: int = 0, step: int = 3600) -> list[Candle]:
    closes = 100 + np.cumsum(np.sin(np.linspace(0, 40, n)) * 0.4 + np.random.RandomState(3).normal(0, 0.2, n))
    return [
        Candle(
            time=start_time + i * step,
            open=float(closes[i]),
            high=float(closes[i]) + 0.4,
            low=float(closes[i]) - 0.4,
            close=float(closes[i]),
            volume=1000.0,
        )
        for i in range(n)
    ]


def _config(**overrides) -> WalkForwardConfig:
    base = {
        "symbol": "TESTUSDT",
        "timeframe": "1h",
        "train_days": 10,
        "validation_days": 3,
        "test_days": 3,
        "folds": 2,
        "simulator": TradeSimulatorConfig(),
    }
    base.update(overrides)
    return WalkForwardConfig(**base)


def test_run_walk_forward_produces_requested_number_of_folds():
    candles = _candles(1200)
    result = run_walk_forward(_config(folds=2), candles, [], [])
    assert len(result.folds) == 2


def test_run_walk_forward_folds_are_sequential_and_non_overlapping():
    candles = _candles(1500)
    result = run_walk_forward(_config(folds=3), candles, [], [])

    for fold in result.folds:
        assert fold.train_start <= fold.train_end
        assert fold.train_end <= fold.validation_start
        assert fold.validation_end <= fold.test_start
        assert fold.test_start <= fold.test_end

    for earlier, later in zip(result.folds, result.folds[1:], strict=False):
        assert earlier.test_end < later.train_start


def test_run_walk_forward_insufficient_data_raises():
    candles = _candles(100)
    with pytest.raises(InsufficientDataError):
        run_walk_forward(_config(folds=5), candles, [], [])


def test_run_walk_forward_rejects_non_positive_days():
    candles = _candles(1200)
    with pytest.raises(InvalidParametersError):
        run_walk_forward(_config(train_days=0), candles, [], [])


def test_run_walk_forward_rejects_non_positive_folds():
    candles = _candles(1200)
    with pytest.raises(InvalidParametersError):
        run_walk_forward(_config(folds=0), candles, [], [])


def test_run_walk_forward_rejects_bad_timeframe():
    candles = _candles(1200)
    with pytest.raises(InvalidParametersError):
        run_walk_forward(_config(timeframe="7h"), candles, [], [])


def test_run_walk_forward_deterministic_same_input_same_output():
    candles = _candles(1200)
    first = run_walk_forward(_config(), candles, [], [])
    second = run_walk_forward(_config(), candles, [], [])

    for fold_a, fold_b in zip(first.folds, second.folds, strict=True):
        assert fold_a.test_result.performance.net_profit == fold_b.test_result.performance.net_profit
        assert len(fold_a.test_result.trades) == len(fold_b.test_result.trades)


def test_run_walk_forward_each_fold_test_segment_has_no_look_ahead():
    """A fold's Test segment result must be unaffected by candles that
    come after it — i.e. by later folds' data. Re-running walk-forward
    with only enough history for the first fold must reproduce fold 0
    exactly."""
    candles = _candles(1500)
    full = run_walk_forward(_config(folds=2), candles, [], [])

    train_bars, validation_bars, test_bars = 240, 72, 72  # 10/3/3 days at 1h
    fold_bars = train_bars + validation_bars + test_bars
    total_needed_full = 250 + fold_bars * 2  # DEFAULT_CANDLE_LOOKBACK + fold_bars * folds
    window_start = len(candles) - total_needed_full
    only_first_fold = candles[window_start : window_start + 250 + fold_bars]

    single = run_walk_forward(_config(folds=1), only_first_fold, [], [])

    assert full.folds[0].test_start == single.folds[0].test_start
    assert full.folds[0].test_result.performance.net_profit == single.folds[0].test_result.performance.net_profit
    assert len(full.folds[0].test_result.trades) == len(single.folds[0].test_result.trades)
