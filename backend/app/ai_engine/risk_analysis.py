"""Risk Analysis (Sprint 8 spec).

A deterministic risk read for the current symbol/interval, built from
the same ATR and Structure-factor levels `risk_engine.py` already uses
— no new indicators:

- **Nearest support/resistance**: read straight from the Structure factor.
- **ATR Risk**: ATR(14) as a percentage of price.
- **Volatility Score**: the existing Volatility factor's 0-100 score.
- **Risk Level**: a coarse LOW/MODERATE/HIGH/EXTREME bucket of ATR Risk.
- **Maximum Recommended Leverage**: a heuristic inversely proportional to
  ATR Risk — the more a symbol typically moves per bar, the less
  leverage it takes to hit a given adverse-move threshold. This is a
  transparent risk-sizing heuristic, not a broker- or backtest-verified
  guarantee.
- **Drawdown Risk**: the stop distance the Risk Engine would use for the
  current direction, as a percentage of price (falls back to the same
  ATR-multiple stop the Risk Engine uses when there's no active
  LONG/SHORT call).
"""

from dataclasses import dataclass

from app.ai_engine.decision_engine import AIDecision
from app.ai_engine.market_context import MarketContext
from app.ai_engine.risk_engine import STOP_ATR_MULTIPLIER
from app.ai_engine.types import clamp, last_valid
from app.services.indicators.atr import atr

ATR_PERIOD = 14
RISK_LEVEL_LOW_PCT = 1.0
RISK_LEVEL_MODERATE_PCT = 2.5
RISK_LEVEL_HIGH_PCT = 5.0
TARGET_RISK_PCT_PER_TRADE = 2.0
MIN_RECOMMENDED_LEVERAGE = 1.0
MAX_RECOMMENDED_LEVERAGE = 20.0


@dataclass(frozen=True)
class RiskAnalysis:
    nearest_support: float | None
    nearest_resistance: float | None
    atr: float | None
    atr_risk_pct: float | None
    volatility_score: float
    risk_level: str
    max_recommended_leverage: float
    drawdown_risk_pct: float | None


def _numeric_or_none(value: object) -> float | None:
    return float(value) if isinstance(value, int | float) and not isinstance(value, bool) else None


def _risk_level(atr_risk_pct: float | None) -> str:
    if atr_risk_pct is None:
        return "MODERATE"
    if atr_risk_pct <= RISK_LEVEL_LOW_PCT:
        return "LOW"
    if atr_risk_pct <= RISK_LEVEL_MODERATE_PCT:
        return "MODERATE"
    if atr_risk_pct <= RISK_LEVEL_HIGH_PCT:
        return "HIGH"
    return "EXTREME"


def analyze_risk(ctx: MarketContext, decision: AIDecision) -> RiskAnalysis:
    structure = decision.factors["structure"]
    support = _numeric_or_none(structure.details.get("nearest_support"))
    resistance = _numeric_or_none(structure.details.get("nearest_resistance"))

    price = ctx.last_close
    atr_last = last_valid(atr(ctx.highs, ctx.lows, ctx.closes, ATR_PERIOD))
    atr_risk_pct = (atr_last / price * 100.0) if atr_last is not None and price > 0 else None

    max_leverage = MIN_RECOMMENDED_LEVERAGE
    if atr_risk_pct is not None and atr_risk_pct > 0:
        max_leverage = clamp(
            TARGET_RISK_PCT_PER_TRADE / atr_risk_pct, MIN_RECOMMENDED_LEVERAGE, MAX_RECOMMENDED_LEVERAGE
        )

    risk_plan = decision.risk
    if risk_plan is not None and risk_plan.entry > 0:
        drawdown_risk_pct = risk_plan.risk_per_unit / risk_plan.entry * 100.0
    elif atr_last is not None and price > 0:
        drawdown_risk_pct = STOP_ATR_MULTIPLIER * atr_last / price * 100.0
    else:
        drawdown_risk_pct = None

    return RiskAnalysis(
        nearest_support=support,
        nearest_resistance=resistance,
        atr=atr_last,
        atr_risk_pct=round(atr_risk_pct, 2) if atr_risk_pct is not None else None,
        volatility_score=round(decision.factors["volatility"].score, 1),
        risk_level=_risk_level(atr_risk_pct),
        max_recommended_leverage=round(max_leverage, 1),
        drawdown_risk_pct=round(drawdown_risk_pct, 2) if drawdown_risk_pct is not None else None,
    )
