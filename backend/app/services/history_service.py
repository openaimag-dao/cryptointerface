"""Historical Behavior tab (Sprint 8 spec).

Every `/api/ai/*` call persists a decision to `ai_analysis` (see
`app/services/ai_repository.py`) — this module replays each of a
symbol's past decisions that had an active LONG/SHORT call against the
*real* candles that followed it, to see whether TP1 or the stop was hit
first (same conservative "stop wins on a same-bar conflict" rule
`app/backtesting/trade_simulator.py` uses). This is a per-signal outcome
check over a bounded horizon, not a continuous strategy backtest — see
`app/backtesting/` for that. It gives Win Rate / average win-loss a real,
non-invented basis, and prepares the data shape Sprint 6 (Paper Trading)
will eventually replace with live position tracking.
"""

from dataclasses import dataclass
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_analysis import AIAnalysis
from app.services.ai_repository import get_recent_analysis
from app.services.market_repository import get_recent_candles
from app.utils.timeframes import timeframe_to_seconds

HISTORY_LIMIT = 50
OUTCOME_HORIZON_BARS = 100

Outcome = Literal["WIN", "LOSS", "OPEN", "NO_TRADE"]


@dataclass(frozen=True)
class SignalOutcome:
    analysis: AIAnalysis
    outcome: Outcome
    pnl_percent: float | None


@dataclass(frozen=True)
class HistorySummary:
    signals: list[SignalOutcome]
    win_rate: float | None
    avg_win_pnl_percent: float | None
    avg_loss_pnl_percent: float | None
    score_history: list[tuple[int, float]]
    confidence_history: list[tuple[int, float]]


def _pnl_percent(direction: str, entry: float, exit_price: float) -> float:
    if direction == "LONG":
        return (exit_price - entry) / entry * 100.0
    return (entry - exit_price) / entry * 100.0


async def _resolve_outcome(db: AsyncSession, symbol: str, interval: str, analysis: AIAnalysis) -> SignalOutcome:
    if analysis.direction == "WAIT" or analysis.entry is None or analysis.stop is None or analysis.tp1 is None:
        return SignalOutcome(analysis=analysis, outcome="NO_TRADE", pnl_percent=None)

    horizon_seconds = timeframe_to_seconds(interval) * OUTCOME_HORIZON_BARS
    candles = await get_recent_candles(
        db, symbol, interval, limit=OUTCOME_HORIZON_BARS, as_of=analysis.time + horizon_seconds
    )
    future_candles = [c for c in candles if c.open_time > analysis.time]

    for candle in future_candles:
        if analysis.direction == "LONG":
            stop_hit = candle.low <= analysis.stop
            tp_hit = candle.high >= analysis.tp1
        else:
            stop_hit = candle.high >= analysis.stop
            tp_hit = candle.low <= analysis.tp1

        if stop_hit:  # conservative: stop wins on a same-bar conflict
            return SignalOutcome(
                analysis=analysis,
                outcome="LOSS",
                pnl_percent=_pnl_percent(analysis.direction, analysis.entry, analysis.stop),
            )
        if tp_hit:
            return SignalOutcome(
                analysis=analysis,
                outcome="WIN",
                pnl_percent=_pnl_percent(analysis.direction, analysis.entry, analysis.tp1),
            )

    return SignalOutcome(analysis=analysis, outcome="OPEN", pnl_percent=None)


async def get_history_summary(
    db: AsyncSession, symbol: str, interval: str, limit: int = HISTORY_LIMIT
) -> HistorySummary:
    rows = await get_recent_analysis(db, symbol, interval, limit=limit)
    signals = [await _resolve_outcome(db, symbol, interval, row) for row in rows]

    resolved = [s for s in signals if s.outcome in ("WIN", "LOSS")]
    wins = [s for s in resolved if s.outcome == "WIN"]
    losses = [s for s in resolved if s.outcome == "LOSS"]

    win_rate = len(wins) / len(resolved) * 100.0 if resolved else None
    avg_win = sum(s.pnl_percent for s in wins) / len(wins) if wins else None
    avg_loss = sum(s.pnl_percent for s in losses) / len(losses) if losses else None

    return HistorySummary(
        signals=list(reversed(signals)),  # newest first for display
        win_rate=round(win_rate, 1) if win_rate is not None else None,
        avg_win_pnl_percent=round(avg_win, 2) if avg_win is not None else None,
        avg_loss_pnl_percent=round(avg_loss, 2) if avg_loss is not None else None,
        score_history=[(row.time, row.score) for row in rows],
        confidence_history=[(row.time, row.confidence) for row in rows],
    )
