"""Builds the data bundle every scoring module reads from.

One DB round-trip per input (candles, funding history, OI history); every
scoring module in `ai_engine/scoring/` then works purely off this
in-memory snapshot — no scoring module does its own I/O, which is what
keeps the whole engine deterministic and unit-testable without a database.
"""

from dataclasses import dataclass

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.funding import FundingRate
from app.models.open_interest import OpenInterest
from app.schemas.candle import Candle
from app.services.market_repository import (
    get_recent_candles,
    get_recent_funding_history,
    get_recent_open_interest_history,
    to_candle_schema,
)

DEFAULT_CANDLE_LOOKBACK = 250  # enough for EMA200 + slope/structure windows to leave warm-up
DEFAULT_FUNDING_LOOKBACK = 20
DEFAULT_OI_LOOKBACK = 20


@dataclass(frozen=True)
class MarketContext:
    symbol: str
    interval: str
    candles: list[Candle]  # ascending (oldest -> newest)
    opens: np.ndarray
    highs: np.ndarray
    lows: np.ndarray
    closes: np.ndarray
    volumes: np.ndarray
    funding_history: list[FundingRate]  # ascending
    oi_history: list[OpenInterest]  # ascending

    @property
    def last_close(self) -> float:
        return float(self.closes[-1])

    @property
    def last_candle_time(self) -> int:
        return self.candles[-1].time


async def build_market_context(
    db: AsyncSession,
    symbol: str,
    interval: str,
    candle_lookback: int = DEFAULT_CANDLE_LOOKBACK,
    funding_lookback: int = DEFAULT_FUNDING_LOOKBACK,
    oi_lookback: int = DEFAULT_OI_LOOKBACK,
) -> MarketContext | None:
    """Returns None if there isn't enough candle history yet to analyze
    (e.g. the Data Engine hasn't backfilled this symbol/interval)."""
    candle_rows = await get_recent_candles(db, symbol, interval, limit=candle_lookback)
    if not candle_rows:
        return None

    candles = [to_candle_schema(row) for row in candle_rows]
    funding_history = await get_recent_funding_history(db, symbol, limit=funding_lookback)
    oi_history = await get_recent_open_interest_history(db, symbol, limit=oi_lookback)

    return MarketContext(
        symbol=symbol,
        interval=interval,
        candles=candles,
        opens=np.array([c.open for c in candles], dtype=float),
        highs=np.array([c.high for c in candles], dtype=float),
        lows=np.array([c.low for c in candles], dtype=float),
        closes=np.array([c.close for c in candles], dtype=float),
        volumes=np.array([c.volume for c in candles], dtype=float),
        funding_history=funding_history,
        oi_history=oi_history,
    )
