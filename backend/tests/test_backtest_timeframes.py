import pytest

from app.backtesting.utils.errors import InvalidParametersError
from app.backtesting.utils.timeframes import (
    MAX_BACKTEST_BARS,
    period_to_bar_count,
    seconds_per_bar,
    validate_backtest_params,
)


def test_seconds_per_bar_known_timeframes():
    assert seconds_per_bar("1h") == 3600
    assert seconds_per_bar("1d") == 86400


def test_seconds_per_bar_unknown_raises():
    with pytest.raises(InvalidParametersError):
        seconds_per_bar("2h")


def test_period_to_bar_count():
    assert period_to_bar_count(90, "1h") == 90 * 24
    assert period_to_bar_count(30, "1d") == 30


def test_validate_backtest_params_accepts_valid_combo():
    validate_backtest_params("BTCUSDT", "1h", 90)  # should not raise


def test_validate_backtest_params_rejects_bad_symbol():
    with pytest.raises(InvalidParametersError):
        validate_backtest_params("", "1h", 30)
    with pytest.raises(InvalidParametersError):
        validate_backtest_params("BTC-USDT", "1h", 30)


def test_validate_backtest_params_rejects_bad_timeframe():
    with pytest.raises(InvalidParametersError):
        validate_backtest_params("BTCUSDT", "3h", 30)


def test_validate_backtest_params_rejects_bad_period():
    with pytest.raises(InvalidParametersError):
        validate_backtest_params("BTCUSDT", "1h", 45)


def test_validate_backtest_params_rejects_over_max_bars():
    with pytest.raises(InvalidParametersError):
        validate_backtest_params("BTCUSDT", "1m", 365)


def test_max_backtest_bars_is_a_sane_positive_bound():
    assert MAX_BACKTEST_BARS > 0
