"""Timeframe/period arithmetic shared by the engine, strategy runner, and
API layer — the single place that knows "how many bars is 90 days of 1h
candles" so that logic isn't duplicated (and doesn't drift) across them.

Reuses `app.utils.timeframes.TIMEFRAME_SECONDS` (already the app-wide
timeframe-to-seconds mapping, used by the LLM/liquidations APIs) rather
than defining a second one.
"""

from app.backtesting.utils.errors import InvalidParametersError
from app.utils.timeframes import TIMEFRAME_SECONDS

SUPPORTED_TIMEFRAMES = tuple(TIMEFRAME_SECONDS)
SUPPORTED_PERIOD_DAYS = (30, 90, 180, 365)

# A pure-Python bar-by-bar replay loop realistically does low hundreds to
# low thousands of bars/second (each bar re-runs the full Decision Engine —
# every scoring module, confidence, risk plan). Past this many bars a
# single HTTP request would run long enough to be a poor experience (and a
# DB-connection-holding request never wants to run for tens of minutes) —
# reject up front with a clear message instead of hanging silently. See
# backend/README.md's Backtesting Engine "Limitations" section.
MAX_BACKTEST_BARS = 50_000


def seconds_per_bar(timeframe: str) -> int:
    if timeframe not in TIMEFRAME_SECONDS:
        raise InvalidParametersError(
            f"Unsupported timeframe {timeframe!r} — must be one of {', '.join(SUPPORTED_TIMEFRAMES)}"
        )
    return TIMEFRAME_SECONDS[timeframe]


def period_to_bar_count(period_days: int, timeframe: str) -> int:
    """How many closed bars fall within `period_days` of a given
    timeframe — e.g. 90 days of 1h candles is 90 * 24 = 2160 bars."""
    bar_seconds = seconds_per_bar(timeframe)
    return (period_days * 24 * 60 * 60) // bar_seconds


def validate_symbol_and_timeframe(symbol: str, timeframe: str) -> None:
    if not symbol or not symbol.isalnum():
        raise InvalidParametersError(f"Invalid symbol {symbol!r}")
    if timeframe not in SUPPORTED_TIMEFRAMES:
        raise InvalidParametersError(
            f"Unsupported timeframe {timeframe!r} — must be one of {', '.join(SUPPORTED_TIMEFRAMES)}"
        )


def validate_backtest_params(symbol: str, timeframe: str, period_days: int) -> None:
    validate_symbol_and_timeframe(symbol, timeframe)
    if period_days not in SUPPORTED_PERIOD_DAYS:
        raise InvalidParametersError(f"Unsupported period {period_days} days — must be one of {SUPPORTED_PERIOD_DAYS}")
    bar_count = period_to_bar_count(period_days, timeframe)
    if bar_count > MAX_BACKTEST_BARS:
        raise InvalidParametersError(
            f"{period_days} days of {timeframe} candles is {bar_count} bars, over the "
            f"{MAX_BACKTEST_BARS}-bar limit for a single backtest run — pick a shorter "
            "period or a coarser timeframe."
        )
