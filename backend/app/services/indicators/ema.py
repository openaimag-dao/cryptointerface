import numpy as np


def ema(values: np.ndarray, period: int) -> np.ndarray:
    """Exponential moving average. First `period - 1` entries are NaN."""
    n = len(values)
    result = np.full(n, np.nan)
    if n < period:
        return result

    alpha = 2.0 / (period + 1)
    seed = np.mean(values[:period])
    result[period - 1] = seed

    prev = seed
    for i in range(period, n):
        prev = values[i] * alpha + prev * (1 - alpha)
        result[i] = prev

    return result
