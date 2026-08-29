from datetime import UTC, datetime

import pytest

from app.services.news_event_repository import (
    assign_to_event,
    get_dedup_candidates,
    get_event_articles,
    get_event_by_id,
)
from app.services.news_repository import insert_article

NOW = int(datetime.now(UTC).timestamp())


async def _insert(db_session, *, url: str, title: str, published_at: int = NOW, topic: str = "AI"):
    await insert_article(
        db_session,
        source="Test Source",
        title=title,
        summary="Summary",
        url=url,
        published_at=published_at,
        language="en",
        symbols=[],
        impact_score=50.0,
        sentiment="NEUTRAL",
        category="Market",
        portal_topic=topic,
    )
    from sqlalchemy import select

    from app.models.news import NewsArticle

    result = await db_session.execute(select(NewsArticle).where(NewsArticle.url == url))
    return result.scalars().one()


@pytest.mark.asyncio
async def test_get_dedup_candidates_excludes_the_article_itself(db_session):
    article = await _insert(db_session, url="https://example.com/a", title="OpenAI launches new AI model")

    candidates = await get_dedup_candidates(db_session, article)

    assert article not in candidates


@pytest.mark.asyncio
async def test_get_dedup_candidates_excludes_a_different_topic(db_session):
    article = await _insert(db_session, url="https://example.com/a", title="OpenAI launches new AI model", topic="AI")
    await _insert(db_session, url="https://example.com/b", title="Bitcoin rallies hard", topic="CRYPTO")

    candidates = await get_dedup_candidates(db_session, article)

    assert candidates == []


@pytest.mark.asyncio
async def test_get_dedup_candidates_excludes_articles_outside_the_time_window(db_session):
    article = await _insert(db_session, url="https://example.com/a", title="OpenAI launches new AI model")
    await _insert(
        db_session,
        url="https://example.com/b",
        title="OpenAI unveils new AI model",
        published_at=NOW - 100 * 3600,  # 100h ago, outside the 48h window
    )

    candidates = await get_dedup_candidates(db_session, article)

    assert candidates == []


@pytest.mark.asyncio
async def test_assign_to_event_returns_none_when_nothing_similar(db_session):
    article = await _insert(db_session, url="https://example.com/a", title="OpenAI launches new AI model")

    event = await assign_to_event(db_session, article)

    assert event is None
    assert article.news_event_id is None


@pytest.mark.asyncio
async def test_assign_to_event_creates_a_new_event_for_two_similar_articles(db_session):
    first = await _insert(db_session, url="https://example.com/a", title="OpenAI launches new flagship AI model")
    second = await _insert(
        db_session, url="https://example.com/b", title="OpenAI unveils new flagship AI model to the public"
    )

    await assign_to_event(db_session, first)
    event = await assign_to_event(db_session, second)

    assert event is not None
    assert first.news_event_id == event.id
    assert second.news_event_id == event.id


@pytest.mark.asyncio
async def test_assign_to_event_joins_the_existing_event_for_a_third_similar_article(db_session):
    first = await _insert(db_session, url="https://example.com/a", title="OpenAI launches new flagship AI model")
    second = await _insert(
        db_session, url="https://example.com/b", title="OpenAI unveils new flagship AI model to the public"
    )
    third = await _insert(
        db_session, url="https://example.com/c", title="OpenAI debuts new flagship AI model worldwide"
    )

    first_event = await assign_to_event(db_session, first)
    await assign_to_event(db_session, second)
    third_event = await assign_to_event(db_session, third)

    assert first_event is not None
    assert third_event is not None
    assert third_event.id == first_event.id

    articles = await get_event_articles(db_session, first_event.id)
    assert {a.id for a in articles} == {first.id, second.id, third.id}


@pytest.mark.asyncio
async def test_assign_to_event_is_idempotent_for_an_already_grouped_article(db_session):
    first = await _insert(db_session, url="https://example.com/a", title="OpenAI launches new flagship AI model")
    second = await _insert(
        db_session, url="https://example.com/b", title="OpenAI unveils new flagship AI model to the public"
    )
    await assign_to_event(db_session, first)
    event = await assign_to_event(db_session, second)

    # Re-running on an article that already has an event must not error or
    # create a duplicate event.
    same_event = await assign_to_event(db_session, second)

    assert same_event is not None
    assert same_event.id == event.id


@pytest.mark.asyncio
async def test_get_event_by_id_returns_none_for_unknown_id(db_session):
    assert await get_event_by_id(db_session, 999999) is None


@pytest.mark.asyncio
async def test_event_primary_article_is_the_earliest_published(db_session):
    later = await _insert(
        db_session, url="https://example.com/a", title="OpenAI launches new flagship AI model", published_at=NOW
    )
    earlier = await _insert(
        db_session,
        url="https://example.com/b",
        title="OpenAI unveils new flagship AI model to the public",
        published_at=NOW - 3600,
    )

    # Both articles exist before either is assigned, so whichever is
    # processed first still finds the other as a dedup candidate.
    event = await assign_to_event(db_session, earlier)

    assert event is not None
    assert event.primary_article_id == earlier.id
    assert later.news_event_id == event.id
