import numpy as np

from app.services.indicators.rsi import rsi


def _rolling_min_max(values: np.ndarray, period: int) -> tuple[np.ndarray, np.ndarray]:
    n = len(values)
    roll_min = np.full(n, np.nan)
    roll_max = np.full(n, np.nan)
    for i in range(period - 1, n):
        window = values[i - period + 1 : i + 1]
        if np.isnan(window).any():
            continue
        roll_min[i] = np.min(window)
        roll_max[i] = np.max(window)
    return roll_min, roll_max


def _sma(values: np.ndarray, period: int) -> np.ndarray:
    n = len(values)
    result = np.full(n, np.nan)
    for i in range(period - 1, n):
        window = values[i - period + 1 : i + 1]
        if np.isnan(window).any():
            continue
        result[i] = np.mean(window)
    return result


def stoch_rsi(
    close: np.ndarray, period: int = 14, smooth_k: int = 3, smooth_d: int = 3
) -> tuple[np.ndarray, np.ndarray]:
    """Stochastic RSI. Returns (%K, %D) on a 0-100 scale."""
    rsi_values = rsi(close, period)
    roll_min, roll_max = _rolling_min_max(rsi_values, period)

    with np.errstate(invalid="ignore", divide="ignore"):
        raw_stoch_rsi = np.where(
            (roll_max - roll_min) > 0,
            (rsi_values - roll_min) / (roll_max - roll_min) * 100,
            np.nan,
        )

    k = _sma(raw_stoch_rsi, smooth_k)
    d = _sma(k, smooth_d)
    return k, d
