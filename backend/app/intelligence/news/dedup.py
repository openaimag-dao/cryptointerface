"""Deterministic multi-source event deduplication — same philosophy as
`classifier.py`: no LLM call per article, a keyword/heuristic approach
that's fast, free, and auditable.

If 5 sources all publish about the same real-world event within a short
window, this groups their articles under one `NewsEvent` (see
app/models/news_event.py) instead of the portal showing 5 near-identical
cards. Matching is title-similarity (Jaccard over normalized word sets)
within a time window — real entity-based matching lands in Q4 once
`app/intelligence/llm/news_processing.py` extracts entities; this doesn't
block on that landing first.
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
