"""Deterministic multi-source event deduplication — same philosophy as
`classifier.py`: no LLM call per article, a keyword/heuristic approach
that's fast, free, and auditable.

If 5 sources all publish about the same real-world event within a short
window, this groups their articles under one `NewsEvent` (see
app/models/news_event.py) instead of the portal showing 5 near-identical
cards. Matching is title-similarity (Jaccard over normalized word sets)
within a time window. `app/intelligence/llm/news_processing.py` (Q4) now
extracts entities per article, but matching here is still title-only —
upgrading to entity-aware matching is future work, not required for this
to be useful today.
"""

import re

from app.models.news import NewsArticle

SIMILARITY_THRESHOLD = 0.5
TIME_WINDOW_HOURS = 48

_NON_WORD_RE = re.compile(r"[^a-z0-9]+")

# Common words that appear in most headlines regardless of topic — including
# them would inflate similarity between genuinely unrelated articles.
_STOPWORDS = frozenset(
    {
        "a", "an", "the", "of", "in", "on", "at", "to", "for", "and", "or", "but", "with", "from",
        "as", "is", "are", "was", "were", "be", "been", "by", "it", "its", "this", "that", "after",
        "over", "up", "down", "new", "says", "said", "will", "how", "why", "what",
    }
)


def normalize_title_tokens(title: str) -> set[str]:
    words = _NON_WORD_RE.sub(" ", title.lower()).split()
    return {word for word in words if word not in _STOPWORDS and len(word) > 2}


def title_similarity(a: str, b: str) -> float:
    tokens_a = normalize_title_tokens(a)
    tokens_b = normalize_title_tokens(b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def find_best_candidate(article: NewsArticle, candidates: list[NewsArticle]) -> NewsArticle | None:
    """Pure matching logic given an already-fetched candidate pool (see
    app/services/news_event_repository.py for how that pool is built) —
    picks the most similar candidate at or above SIMILARITY_THRESHOLD, or
    None if nothing matches closely enough."""
    best: NewsArticle | None = None
    best_score = 0.0
    for candidate in candidates:
        if candidate.id == article.id:
            continue
        score = title_similarity(article.title, candidate.title)
        if score >= SIMILARITY_THRESHOLD and score > best_score:
            best = candidate
            best_score = score
    return best


# Weights for compute_importance_score — deliberately simple and auditable
# rather than tuned: the classifier's impact_score (0-100, keyword-based —
# see classifier.py) already captures "how big a deal does this look like",
# and independent-source corroboration is the clearest cheap signal that a
# story is real/significant rather than one outlet's spin. Capped at 5
# sources so a 20-source wire-copy story doesn't dominate a 2-source scoop
# that's actually more novel.
_IMPACT_WEIGHT = 6.0
_SOURCE_WEIGHT_PER_ARTICLE = 0.8
_MAX_SOURCES_COUNTED = 5


def compute_importance_score(article_impact_scores: list[float]) -> float:
    """0-10 scale (see spec section 11's "Importance: 9.4/10") from the
    grouped event's own articles — no new facts, just a deterministic
    combination of numbers the classifier and dedup engine already
    computed. Recomputed every time an article joins or creates an event
    (app/services/news_event_repository.py), so it grows as more sources
    corroborate the story."""
    if not article_impact_scores:
        return 0.0
    impact_component = (max(article_impact_scores) / 100.0) * _IMPACT_WEIGHT
    source_component = min(len(article_impact_scores), _MAX_SOURCES_COUNTED) * _SOURCE_WEIGHT_PER_ARTICLE
    return round(min(impact_component + source_component, 10.0), 1)
