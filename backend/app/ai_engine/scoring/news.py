"""News Engine (Sprint 3 stub).

Sprint 3 has no real news/sentiment feed. This module exists so the rest
of the engine already has a stable slot for news-driven sentiment —
Sprint 4 wires up real news ingestion (and later, whale-wallet activity)
and replaces the body of `score_news`, without any caller needing to
change.

Always returns a neutral, zero-conviction read. `market_score.py` gives
this factor zero weight until real data lands, so the stub cannot move
the aggregate Market Score or Decision.
"""

from app.ai_engine.types import FactorScore, make_factor_score


def score_news() -> FactorScore:
    reasons = [
        "News sentiment analysis is not yet integrated "
        "— this is a neutral Sprint 4 stub with zero weight in the aggregate score"
    ]
    details: dict[str, float | str | bool | int] = {"stub": True}
    factor = make_factor_score("news", 50.0, reasons, details)
    factor.details["news_score"] = factor.score
    factor.details["news_direction"] = factor.direction
    factor.details["news_strength"] = factor.strength
    return factor
