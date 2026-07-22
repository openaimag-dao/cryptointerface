"""Correlation module (Sprint 8 spec) — how closely one asset's price
moves with a set of reference assets, using the Pearson correlation
coefficient over period-over-period returns.

Two tiers, both real computations (never a fabricated number), differing
only in how much history backs them today:

- **Crypto references (BTC, ETH)** — computed from this app's own candle
  history (`app/services/market_repository.py`), the same data Sprint 2's
  Data Engine already ingests. Real today.
- **TradFi references (NASDAQ, S&P 500, Gold, DXY)** — computed from the
  Sprint 4 Macro Engine's `macro_data` history
  (`app/services/macro_repository.py`). The architecture is exactly the
  same computation, just against a thinner data source: the Macro Engine
  only started collecting recently and polls every few hours, so most
  symbols won't yet have `CORRELATION_MIN_DATA_POINTS` matched readings.
  When that's the case this returns `None` rather than a correlation
  computed from too few points to mean anything — the frontend shows
  "insufficient data yet," not a number that looks precise but isn't.
"""

from dataclasses import dataclass

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.macro_repository import get_history
from app.services.market_repository import get_recent_candles

# Below this many matched return-pairs, a Pearson coefficient is more
# noise than signal — report "not enough data" instead of a number.
CORRELATION_MIN_DATA_POINTS = 20
CORRELATION_LOOKBACK_CANDLES = 200

CRYPTO_REFERENCE_SYMBOLS: dict[str, str] = {"BTC": "BTCUSDT", "ETH": "ETHUSDT"}
MACRO_REFERENCE_INDICATORS: dict[str, str] = {"NASDAQ": "nasdaq", "SP500": "sp500", "GOLD": "gold", "DXY": "dxy"}


@dataclass(frozen=True)
class CorrelationReading:
    reference: str
    coefficient: float | None  # None = not enough matched data points yet
    data_points: int


def _pearson(a: list[float], b: list[float]) -> float | None:
    if len(a) < CORRELATION_MIN_DATA_POINTS or len(a) != len(b):
        return None
    arr_a, arr_b = np.array(a), np.array(b)
    if np.std(arr_a) == 0 or np.std(arr_b) == 0:
        return None
    return float(np.corrcoef(arr_a, arr_b)[0, 1])


def _returns(values: list[float]) -> list[float]:
    """Period-over-period % returns — correlation is computed on returns,
    not raw levels, so two assets both simply trending up over the window
    don't read as artificially correlated."""
    return [(values[i] - values[i - 1]) / values[i - 1] for i in range(1, len(values)) if values[i - 1] != 0]


async def _crypto_correlation(
    db: AsyncSession, symbol: str, timeframe: str, reference_symbol: str, label: str
) -> CorrelationReading | None:
    if symbol == reference_symbol:
        return None  # never correlate an asset against itself

    target_rows = await get_recent_candles(db, symbol, timeframe, limit=CORRELATION_LOOKBACK_CANDLES)
    reference_rows = await get_recent_candles(db, reference_symbol, timeframe, limit=CORRELATION_LOOKBACK_CANDLES)
    if not target_rows or not reference_rows:
        return CorrelationReading(reference=label, coefficient=None, data_points=0)

    # Align by candle open_time — the two series may not have identical
    # gaps (thin/interrupted backfills are common in this environment).
    target_by_time = {row.open_time: row.close for row in target_rows}
    reference_by_time = {row.open_time: row.close for row in reference_rows}
    shared_times = sorted(set(target_by_time) & set(reference_by_time))

    target_returns = _returns([target_by_time[t] for t in shared_times])
    reference_returns = _returns([reference_by_time[t] for t in shared_times])

    coefficient = _pearson(target_returns, reference_returns)
    return CorrelationReading(reference=label, coefficient=coefficient, data_points=len(target_returns))


async def _macro_correlation(
    db: AsyncSession, symbol: str, timeframe: str, indicator: str, label: str
) -> CorrelationReading:
    candle_rows = await get_recent_candles(db, symbol, timeframe, limit=CORRELATION_LOOKBACK_CANDLES)
    macro_points = await get_history(db, indicator, limit=CORRELATION_LOOKBACK_CANDLES)
    if not candle_rows or not macro_points:
        return CorrelationReading(reference=label, coefficient=None, data_points=0)

    # Match each macro reading to the nearest candle at or before it —
    # the macro poll cadence (hours) is coarser than most candle
    # timeframes, so an exact-timestamp join would almost always miss.
    candles_sorted = sorted(candle_rows, key=lambda c: c.open_time)
    candle_times = [c.open_time for c in candles_sorted]
    candle_closes = [c.close for c in candles_sorted]

    matched_prices: list[float] = []
    matched_macro: list[float] = []
    for point in sorted(macro_points, key=lambda p: p.fetched_at):
        idx = _last_index_at_or_before(candle_times, point.fetched_at)
        if idx is not None:
            matched_prices.append(candle_closes[idx])
            matched_macro.append(point.value)

    price_returns = _returns(matched_prices)
    macro_returns = _returns(matched_macro)
    coefficient = _pearson(price_returns, macro_returns)
    return CorrelationReading(reference=label, coefficient=coefficient, data_points=len(price_returns))


def _last_index_at_or_before(sorted_times: list[int], target: int) -> int | None:
    """Index of the latest entry in `sorted_times` that is <= `target`,
    or None if every entry is after it."""
    best: int | None = None
    for i, t in enumerate(sorted_times):
        if t <= target:
            best = i
        else:
            break
    return best


async def compute_correlations(db: AsyncSession, symbol: str, timeframe: str = "1h") -> list[CorrelationReading]:
    readings: list[CorrelationReading] = []

    for label, reference_symbol in CRYPTO_REFERENCE_SYMBOLS.items():
        reading = await _crypto_correlation(db, symbol, timeframe, reference_symbol, label)
        if reading is not None:
            readings.append(reading)

    for label, indicator in MACRO_REFERENCE_INDICATORS.items():
        readings.append(await _macro_correlation(db, symbol, timeframe, indicator, label))

    return readings
