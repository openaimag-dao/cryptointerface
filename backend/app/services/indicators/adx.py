import numpy as np

from app.services.indicators.atr import true_range


def _wilder_smooth(values: np.ndarray, period: int, start_index: int) -> np.ndarray:
    n = len(values)
    result = np.full(n, np.nan)
    if start_index + period > n:
        return result

    seed = np.sum(values[start_index : start_index + period])
    result[start_index + period - 1] = seed

    prev = seed
    for i in range(start_index + period, n):
        prev = prev - (prev / period) + values[i]
        result[i] = prev

    return result


def adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """Average Directional Index (Wilder). First ~`2 * period - 1` entries are NaN."""
    n = len(close)
    result = np.full(n, np.nan)
    if n < 2 * period:
        return result

    up_move = np.zeros(n)
    down_move = np.zeros(n)
    up_move[1:] = high[1:] - high[:-1]
    down_move[1:] = low[:-1] - low[1:]

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    tr = true_range(high, low, close)
    tr[0] = 0.0

    smoothed_tr = _wilder_smooth(tr, period, 1)
    smoothed_plus_dm = _wilder_smooth(plus_dm, period, 1)
    smoothed_minus_dm = _wilder_smooth(minus_dm, period, 1)

    with np.errstate(invalid="ignore", divide="ignore"):
        plus_di = np.where(smoothed_tr > 0, 100 * smoothed_plus_dm / smoothed_tr, np.nan)
        minus_di = np.where(smoothed_tr > 0, 100 * smoothed_minus_dm / smoothed_tr, np.nan)
        di_sum = plus_di + minus_di
        dx = np.where(di_sum > 0, 100 * np.abs(plus_di - minus_di) / di_sum, np.nan)

    first_dx_index = period
    valid_dx = dx[first_dx_index:]

    # First ADX value is a simple average of the first `period` DX values (Wilder's method),
    # subsequent values are the running smoothed average.
    if len(valid_dx) >= period:
        first_adx = np.mean(valid_dx[:period])
        result[first_dx_index + period - 1] = first_adx
        prev = first_adx
        for i in range(period, len(valid_dx)):
            if np.isnan(valid_dx[i]):
                continue
            prev = (prev * (period - 1) + valid_dx[i]) / period
            result[first_dx_index + i] = prev

    return result
