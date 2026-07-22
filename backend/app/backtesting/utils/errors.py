"""Backtesting Engine error hierarchy — every failure mode the spec calls
out explicitly (недостаток исторических данных / неверные параметры /
ошибки БД / ошибки расчета) maps to one of these, so `engine.py` can catch
`BacktestError` at the top level, persist a clean `FAILED` row with
`error_message`, and let anything unexpected (a real bug) still raise.
"""


class BacktestError(Exception):
    """Base class for every backtest-specific failure."""


class InsufficientDataError(BacktestError):
    """Not enough historical candles on file for the requested symbol,
    timeframe, and period — includes exactly how much is available so the
    caller can pick a shorter period or a coarser timeframe."""


class InvalidParametersError(BacktestError):
    """A request parameter is out of range or nonsensical (unknown
    timeframe, non-positive balance, a period too large to simulate bar
    by bar in one request — see `MAX_BACKTEST_BARS`)."""


class ComputationError(BacktestError):
    """A metric or simulation step failed in a way that isn't a data or
    parameter problem (e.g. an unexpected NaN/Inf from an intermediate
    calculation) — distinct from the two above so it's never mistaken for
    a user-fixable input error."""
