from datetime import UTC, datetime

from app.intelligence.news.dedup import find_best_candidate, normalize_title_tokens, title_similarity
from app.models.news import NewsArticle


def _article(id_: int, title: str) -> NewsArticle:
    article = NewsArticle(
        source="Test",
        title=title,
        summary="Summary",
        url=f"https://example.com/{id_}",
        published_at=int(datetime.now(UTC).timestamp()),
        language="en",
        symbols=[],
        impact_score=50.0,
        sentiment="NEUTRAL",
        category="Market",
    )
    article.id = id_
    return article


def test_normalize_title_tokens_lowercases_and_strips_stopwords():
    tokens = normalize_title_tokens("The Bitcoin ETF Inflows Hit a Record High")
    assert "the" not in tokens
    assert "a" not in tokens
    assert "bitcoin" in tokens
    assert "inflows" in tokens


def test_title_similarity_is_1_for_identical_titles():
    assert title_similarity("Bitcoin ETF inflows hit record high", "Bitcoin ETF inflows hit record high") == 1.0


def test_title_similarity_is_0_for_unrelated_titles():
    score = title_similarity("Bitcoin ETF inflows hit record high", "Robotics startup raises Series A funding")
    assert score == 0.0


def test_title_similarity_is_high_for_paraphrased_coverage_of_the_same_event():
    a = "OpenAI launches new flagship AI model"
    b = "OpenAI unveils new flagship AI model to the public"
    assert title_similarity(a, b) >= 0.5


def test_title_similarity_returns_0_for_empty_titles():
    assert title_similarity("", "Bitcoin rallies") == 0.0


def test_find_best_candidate_picks_the_most_similar_match():
    article = _article(1, "OpenAI launches new flagship AI model")
    close_match = _article(2, "OpenAI unveils new flagship AI model to the public")
    unrelated = _article(3, "Robotics startup raises Series A funding")

    best = find_best_candidate(article, [unrelated, close_match])

    assert best is close_match


def test_find_best_candidate_returns_none_when_nothing_matches():
    article = _article(1, "OpenAI launches new flagship AI model")
    unrelated = _article(2, "Robotics startup raises Series A funding")

    assert find_best_candidate(article, [unrelated]) is None


def test_find_best_candidate_excludes_the_article_itself():
    article = _article(1, "OpenAI launches new flagship AI model")

    assert find_best_candidate(article, [article]) is None
