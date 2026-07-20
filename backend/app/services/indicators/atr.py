import numpy as np


def true_range(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    n = len(high)
    tr = np.full(n, np.nan)
    if n == 0:
        return tr

    tr[0] = high[0] - low[0]
    prev_close = close[:-1]
    hi_lo = high[1:] - low[1:]
    hi_pc = np.abs(high[1:] - prev_close)
    lo_pc = np.abs(low[1:] - prev_close)
    tr[1:] = np.maximum(hi_lo, np.maximum(hi_pc, lo_pc))
    return tr


def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """Wilder's Average True Range. First `period - 1` entries are NaN."""
    n = len(close)
    result = np.full(n, np.nan)
    if n < period:
        return result

    tr = true_range(high, low, close)
    result[period - 1] = np.mean(tr[:period])

    prev = result[period - 1]
    for i in range(period, n):
        prev = (prev * (period - 1) + tr[i]) / period
        result[i] = prev

    return result
