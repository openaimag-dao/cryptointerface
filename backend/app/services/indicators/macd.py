import numpy as np

from app.services.indicators.ema import ema


def _ema_skip_leading_nan(values: np.ndarray, period: int) -> np.ndarray:
    """EMA that tolerates leading NaNs in `values` (e.g. another EMA's warm-up)."""
    result = np.full(len(values), np.nan)
    valid_mask = ~np.isnan(values)
    if not valid_mask.any():
        return result
    first_valid = int(np.argmax(valid_mask))
    sub_result = ema(values[first_valid:], period)
    result[first_valid:] = sub_result
    return result


def macd(
    close: np.ndarray, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Returns (macd_line, signal_line, histogram)."""
    ema_fast = ema(close, fast_period)
    ema_slow = ema(close, slow_period)
    macd_line = ema_fast - ema_slow
    signal_line = _ema_skip_leading_nan(macd_line, signal_period)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram
