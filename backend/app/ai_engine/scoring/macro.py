"""Macro Engine (Sprint 3 stub).

Sprint 3 has no real macro data feed. This module exists so the rest of
the engine (`market_score.py`, `reason_generator.py`, the API response
shape) already has a stable slot for BTC Dominance, DXY, Gold, S&P 500,
NASDAQ, and VIX — Sprint 4 wires up the real feeds and replaces the body
of `score_macro`, without any caller needing to change.

Always returns a neutral, zero-conviction read. `market_score.py` gives
this factor zero weight until real data lands, so the stub cannot move
the aggregate Market Score or Decision.
"""

from app.ai_engine.types import FactorScore, make_factor_score

STUB_INPUTS = ("btc_dominance", "dxy", "gold", "sp500", "nasdaq", "vix")


def score_macro() -> FactorScore:
    reasons = [
        "Macro data (BTC Dominance, DXY, Gold, S&P 500, NASDAQ, VIX) is not yet integrated "
        "— this is a neutral Sprint 4 stub with zero weight in the aggregate score"
    ]
    details: dict[str, float | str | bool | int] = {"stub": True, "pending_inputs": ", ".join(STUB_INPUTS)}
    factor = make_factor_score("macro", 50.0, reasons, details)
    factor.details["macro_score"] = factor.score
    factor.details["macro_direction"] = factor.direction
    factor.details["macro_strength"] = factor.strength
    return factor
