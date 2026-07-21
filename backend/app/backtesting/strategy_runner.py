"""Replays the unmodified Sprint 3 Decision Engine (`analyze_market()`)
bar by bar over already-fetched historical data.

**No look-ahead, by construction**: bar `i`'s decision is built from a
fixed-size window of candles `[i - candle_lookback + 1, i]` — the exact
same "how many bars does the engine look at" the real-time API uses (see
`app/ai_engine/market_context.py`'s `DEFAULT_CANDLE_LOOKBACK`) — and
funding/open-interest history is cut off at that bar's own timestamp.
Nothing later than bar `i` is ever visible when computing bar `i`'s
decision. Macro/News/Whale snapshots are always `None` here — see
`build_market_context_from_data`'s docstring and `backend/README.md`'s
Backtesting Engine "Limitations" section for why (no point-in-time
history exists for those Sprint 4 inputs yet).

**One bulk fetch, not N**: the caller (`engine.py`) loads the full
candle/funding/OI history for the run once; this module only slices
already-in-memory Python lists per bar, so replaying tens of thousands of
bars never issues a database query per bar.
"""

from collections.abc import Iterator
from dataclasses import dataclass

from app.ai_engine.decision_engine import AIDecision, analyze_market
from app.ai_engine.market_context import (
    DEFAULT_CANDLE_LOOKBACK,
    DEFAULT_FUNDING_LOOKBACK,
    DEFAULT_OI_LOOKBACK,
    build_market_context_from_data,
)
from app.models.funding import FundingRate
from app.models.open_interest import OpenInterest
from app.schemas.candle import Candle


@dataclass(frozen=True)
class BarDecision:
    bar: Candle
    decision: AIDecision | None  # None during warm-up, before candle_lookback bars have accumulated


def iter_decisions(
    symbol: str,
    interval: str,
    candles: list[Candle],
    funding_history: list[FundingRate],
    oi_history: list[OpenInterest],
    candle_lookback: int = DEFAULT_CANDLE_LOOKBACK,
    funding_lookback: int = DEFAULT_FUNDING_LOOKBACK,
    oi_lookback: int = DEFAULT_OI_LOOKBACK,
) -> Iterator[BarDecision]:
    """`candles` must be ascending and include `candle_lookback - 1` bars
    of warm-up before the first bar a caller actually wants a decision
    for — `engine.py` fetches exactly that padding. Bars before enough
    warm-up has accumulated yield `decision=None`, same as the real-time
    API's "not enough history yet" response.
    """
    funding_idx = 0
    oi_idx = 0

    for i, bar in enumerate(candles):
        if i < candle_lookback - 1:
            yield BarDecision(bar=bar, decision=None)
            continue

        window = candles[i - candle_lookback + 1 : i + 1]
        cutoff = bar.time

        while funding_idx < len(funding_history) and funding_history[funding_idx].funding_time <= cutoff:
            funding_idx += 1
        funding_window = funding_history[max(0, funding_idx - funding_lookback) : funding_idx]

        while oi_idx < len(oi_history) and oi_history[oi_idx].timestamp <= cutoff:
            oi_idx += 1
        oi_window = oi_history[max(0, oi_idx - oi_lookback) : oi_idx]

        ctx = build_market_context_from_data(
            symbol,
            interval,
            window,
            funding_window,
            oi_window,
            macro_snapshot=None,
            news_snapshot=None,
            whale_snapshot=None,
        )
        yield BarDecision(bar=bar, decision=analyze_market(ctx))
