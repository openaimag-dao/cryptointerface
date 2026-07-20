import numpy as np


def obv(close: np.ndarray, volume: np.ndarray) -> np.ndarray:
    """On-Balance Volume, cumulative from the start of the series."""
    n = len(close)
    result = np.zeros(n)
    if n == 0:
        return result

    result[0] = volume[0]
    for i in range(1, n):
        if close[i] > close[i - 1]:
            result[i] = result[i - 1] + volume[i]
        elif close[i] < close[i - 1]:
            result[i] = result[i - 1] - volume[i]
        else:
            result[i] = result[i - 1]

    return result
