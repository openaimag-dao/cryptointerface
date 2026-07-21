"""Real AI signals — one row per watchlist symbol with an actionable
(LONG/SHORT) read from the deterministic AI Decision Engine (see
`app/ai_engine/`). Symbols currently reading WAIT are omitted: a "signal"
implies a directional call, and WAIT has no risk plan to show.

This is a read-only batched view over the same engine `/api/ai/decision`
uses — it does not persist to `ai_analysis` on every poll (the frontend
refetches this list every 20s; persisting every symbol on every poll would
flood that history table for no benefit over the per-symbol endpoints,
which already persist when actually inspected).
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_engine.decision_engine import analyze_market
from app.ai_engine.market_context import build_market_context
from app.core.config import get_settings
from app.database.session import get_db
from app.schemas.signal import AiSignal
from app.utils.timeframes import TIMEFRAME_SECONDS

router = APIRouter(prefix="/api/signals", tags=["signals"])
settings = get_settings()


@router.get("", response_model=list[AiSignal])
async def list_signals(
    interval: str = Query("1h", description="One of: " + ", ".join(TIMEFRAME_SECONDS)),
    db: AsyncSession = Depends(get_db),
) -> list[AiSignal]:
    signals: list[AiSignal] = []

    for symbol in settings.symbol_list:
        ctx = await build_market_context(db, symbol, interval)
        if ctx is None:
            continue

        decision = analyze_market(ctx)
        if decision.direction == "WAIT" or decision.risk is None:
            continue

        risk = decision.risk
        signals.append(
            AiSignal(
                id=f"{symbol}-{interval}-{decision.timestamp}",
                symbol=symbol,
                direction=decision.direction,
                confidence=round(decision.confidence, 1),
                entry=risk.entry,
                stop_loss=risk.stop,
                take_profit_1=risk.tp1,
                take_profit_2=risk.tp2,
                take_profit_3=risk.tp3,
                risk_reward=round(risk.risk_reward_tp2, 2),
                reasons=decision.reasons,
                created_at=datetime.fromtimestamp(decision.timestamp, tz=UTC).isoformat(),
                timeframe=interval,
            )
        )

    signals.sort(key=lambda s: s.confidence, reverse=True)
    return signals
