"""News Engine (Sprint 4).

Reads the latest news snapshot for a symbol
(`app/services/news_repository.py::get_news_snapshot_for_symbol()`,
populated by `app/intelligence/news/` — real RSS ingestion classified by
a deterministic keyword classifier, see `classifier.py`'s docstring for
why this isn't an LLM call per article). `market_score.py` was already
shaped for this since Sprint 3 — this file only had to replace the stub
body and the weight moved from 0.00 to a real value.

Score composition (starts at neutral 50): the snapshot's
`avg_sentiment_score` (already 0-100, impact-weighted) is scaled toward
neutral by how much signal actually backs it — few articles or low
average impact pulls the read back toward neutral rather than
overreacting to one throwaway mention.
"""

from app.ai_engine.types import FactorScore, NewsSnapshot, clamp, make_factor_score

MAX_POINTS = 25.0
CONFIDENCE_ARTICLE_CAP = 5  # article counts above this don't add more confidence


def score_news(snapshot: NewsSnapshot | None) -> FactorScore:
    reasons: list[str] = []
    details: dict[str, float | str | bool | int] = {}

    if snapshot is None or snapshot.article_count == 0:
        reasons.append("No relevant news in the last 72h — neutral, zero-conviction read")
        factor = make_factor_score("news", 50.0, reasons, details)
        factor.details["news_score"] = factor.score
        factor.details["news_direction"] = factor.direction
        factor.details["news_strength"] = factor.strength
        return factor

    distance = snapshot.avg_sentiment_score - 50.0  # -50..+50
    confidence_scale = clamp(
        min(snapshot.article_count, CONFIDENCE_ARTICLE_CAP) / CONFIDENCE_ARTICLE_CAP * (snapshot.avg_impact / 100.0),
        0,
        1,
    )
    points = abs(distance) / 50.0 * MAX_POINTS * confidence_scale
    score = 50.0 + (points if distance > 0 else -points if distance < 0 else 0.0)

    direction_word = "net bullish" if distance > 0 else "net bearish" if distance < 0 else "mixed/neutral"
    reasons.append(
        f"{snapshot.article_count} relevant article(s) in the last 72h reading {direction_word} "
        f"(avg impact {snapshot.avg_impact:.0f}/100)"
    )
    details["article_count"] = snapshot.article_count
    details["avg_sentiment_score"] = round(snapshot.avg_sentiment_score, 1)
    details["avg_impact"] = round(snapshot.avg_impact, 1)

    factor = make_factor_score("news", score, reasons, details)
    factor.details["news_score"] = factor.score
    factor.details["news_direction"] = factor.direction
    factor.details["news_strength"] = factor.strength
    return factor
