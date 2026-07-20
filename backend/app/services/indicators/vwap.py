import numpy as np


def vwap(high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray) -> np.ndarray:
    """Cumulative volume-weighted average price over the given candle window.

    This is anchored to the start of the provided series (not a
    session/day-reset VWAP) — the caller decides the window (e.g. "since
    the start of this timeframe's loaded history").
    """
    typical_price = (high + low + close) / 3.0
    cum_pv = np.cumsum(typical_price * volume)
    cum_volume = np.cumsum(volume)
    with np.errstate(invalid="ignore", divide="ignore"):
        result = np.where(cum_volume > 0, cum_pv / cum_volume, np.nan)
    return result
