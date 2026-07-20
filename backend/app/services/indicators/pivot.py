import numpy as np


def pivot_points(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> dict[str, np.ndarray]:
    """Classic floor-trader pivot levels, computed per-candle from the
    *previous* candle's H/L/C (rolling, not calendar-day anchored). Index 0
    is always NaN since it has no prior candle.
    """
    n = len(close)
    pivot = np.full(n, np.nan)
    r1 = np.full(n, np.nan)
    r2 = np.full(n, np.nan)
    r3 = np.full(n, np.nan)
    s1 = np.full(n, np.nan)
    s2 = np.full(n, np.nan)
    s3 = np.full(n, np.nan)

    if n < 2:
        return {"pivot": pivot, "r1": r1, "r2": r2, "r3": r3, "s1": s1, "s2": s2, "s3": s3}

    prev_high = high[:-1]
    prev_low = low[:-1]
    prev_close = close[:-1]

    p = (prev_high + prev_low + prev_close) / 3.0
    pivot[1:] = p
    r1[1:] = 2 * p - prev_low
    s1[1:] = 2 * p - prev_high
    r2[1:] = p + (prev_high - prev_low)
    s2[1:] = p - (prev_high - prev_low)
    r3[1:] = prev_high + 2 * (p - prev_low)
    s3[1:] = prev_low - 2 * (prev_high - p)

    return {"pivot": pivot, "r1": r1, "r2": r2, "r3": r3, "s1": s1, "s2": s2, "s3": s3}
