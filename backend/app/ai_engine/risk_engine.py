"""Risk Engine.

Computes Entry/Stop/TP1-3/Risk-Reward from ATR and the structure factor's
support/resistance levels — never fixed percentages. The stop uses
whichever is tighter-but-still-safe: the nearest swing support/resistance
(with a small ATR buffer beyond it) when it's within a reasonable ATR
multiple of price, otherwise a pure ATR-multiple stop. Take-profit levels
are R-multiples of the resulting risk distance, nudged toward a real
resistance/support level when one falls naturally inside that range.

Returns `None` for a WAIT decision — this engine never proposes a trade
plan without a directional call, and it never executes anything; it only
computes the numbers a human (or a future execution layer) would need.
"""

from dataclasses import dataclass

from app.ai_engine.market_context import MarketContext
from app.ai_engine.types import Direction, FactorScore, last_valid
from app.services.indicators.atr import atr

ATR_PERIOD = 14
STOP_ATR_MULTIPLIER = 1.5
STRUCTURE_BUFFER_ATR_MULTIPLIER = 0.5
MAX_STRUCTURE_ATR_DISTANCE = 3.0
TP1_R_MULTIPLE = 1.5
TP2_R_MULTIPLE = 2.5
TP3_R_MULTIPLE = 4.0
TP2_STRUCTURE_MARGIN_R = 0.1


@dataclass(frozen=True)
class RiskPlan:
    direction: Direction
    entry: float
    stop: float
    tp1: float
    tp2: float
    tp3: float
    risk_per_unit: float
    risk_reward_tp1: float
    risk_reward_tp2: float
    risk_reward_tp3: float


def _numeric_or_none(value: object) -> float | None:
    return float(value) if isinstance(value, int | float) and not isinstance(value, bool) else None


def compute_risk_plan(direction: Direction, ctx: MarketContext, structure: FactorScore) -> RiskPlan | None:
    if direction == "WAIT":
        return None

    atr_last = last_valid(atr(ctx.highs, ctx.lows, ctx.closes, ATR_PERIOD))
    if atr_last is None or atr_last <= 0:
        return None

    entry = ctx.last_close
    support = _numeric_or_none(structure.details.get("nearest_support"))
    resistance = _numeric_or_none(structure.details.get("nearest_resistance"))

    if direction == "LONG":
        if support is not None and 0 < entry - support <= MAX_STRUCTURE_ATR_DISTANCE * atr_last:
            stop = support - STRUCTURE_BUFFER_ATR_MULTIPLIER * atr_last
        else:
            stop = entry - STOP_ATR_MULTIPLIER * atr_last

        risk_per_unit = entry - stop
        if risk_per_unit <= 0:
            return None

        tp1 = entry + TP1_R_MULTIPLE * risk_per_unit
        tp2 = entry + TP2_R_MULTIPLE * risk_per_unit
        tp3 = entry + TP3_R_MULTIPLE * risk_per_unit
        if resistance is not None and entry < resistance < tp3:
            tp2 = max(tp1 + TP2_STRUCTURE_MARGIN_R * risk_per_unit, resistance)
    else:  # SHORT
        if resistance is not None and 0 < resistance - entry <= MAX_STRUCTURE_ATR_DISTANCE * atr_last:
            stop = resistance + STRUCTURE_BUFFER_ATR_MULTIPLIER * atr_last
        else:
            stop = entry + STOP_ATR_MULTIPLIER * atr_last

        risk_per_unit = stop - entry
        if risk_per_unit <= 0:
            return None

        tp1 = entry - TP1_R_MULTIPLE * risk_per_unit
        tp2 = entry - TP2_R_MULTIPLE * risk_per_unit
        tp3 = entry - TP3_R_MULTIPLE * risk_per_unit
        if support is not None and tp3 < support < entry:
            tp2 = min(tp1 - TP2_STRUCTURE_MARGIN_R * risk_per_unit, support)

    return RiskPlan(
        direction=direction,
        entry=entry,
        stop=stop,
        tp1=tp1,
        tp2=tp2,
        tp3=tp3,
        risk_per_unit=risk_per_unit,
        risk_reward_tp1=abs(tp1 - entry) / risk_per_unit,
        risk_reward_tp2=abs(tp2 - entry) / risk_per_unit,
        risk_reward_tp3=abs(tp3 - entry) / risk_per_unit,
    )
