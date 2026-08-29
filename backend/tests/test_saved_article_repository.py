from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.models.news import NewsArticle
from app.services.news_repository import insert_article
from app.services.saved_article_repository import (
    is_article_saved,
    list_saved_articles,
    save_article,
    unsave_article,
)
from app.services.user_repository import create_user


async def _insert_article(db_session, url: str, title: str = "Title") -> int:
    await insert_article(
        db_session,
        source="Test Source",
        title=title,
        summary="Summary",
        url=url,
        published_at=int(datetime.now(UTC).timestamp()),
        language="en",
        symbols=[],
        impact_score=50.0,
        sentiment="NEUTRAL",
        category="Market",
    )
    result = await db_session.execute(select(NewsArticle).where(NewsArticle.url == url))
    return result.scalars().one().id


async def _make_user(db_session, email: str) -> int:
    user = await create_user(db_session, email=email, hashed_password="x", display_name=None)
    return user.id


@pytest.mark.asyncio
async def test_save_article_returns_true_for_a_new_bookmark(db_session):
    user_id = await _make_user(db_session, "a@example.com")
    article_id = await _insert_article(db_session, "https://example.com/a")

    saved = await save_article(db_session, user_id=user_id, article_id=article_id)

    assert saved is True
    assert await is_article_saved(db_session, user_id=user_id, article_id=article_id) is True


@pytest.mark.asyncio
async def test_save_article_is_idempotent(db_session):
    user_id = await _make_user(db_session, "b@example.com")
    article_id = await _insert_article(db_session, "https://example.com/b")

    first = await save_article(db_session, user_id=user_id, article_id=article_id)
    second = await save_article(db_session, user_id=user_id, article_id=article_id)

    assert first is True
    assert second is False


@pytest.mark.asyncio
async def test_list_saved_articles_only_returns_that_users_bookmarks(db_session):
    user_1 = await _make_user(db_session, "c@example.com")
    user_2 = await _make_user(db_session, "d@example.com")
    article_a = await _insert_article(db_session, "https://example.com/c")
    article_b = await _insert_article(db_session, "https://example.com/d")
    await save_article(db_session, user_id=user_1, article_id=article_a)
    await save_article(db_session, user_id=user_2, article_id=article_b)

    user_1_saved = await list_saved_articles(db_session, user_id=user_1)

    assert len(user_1_saved) == 1
    assert user_1_saved[0].id == article_a


@pytest.mark.asyncio
async def test_unsave_article_removes_the_bookmark(db_session):
    user_id = await _make_user(db_session, "e@example.com")
    article_id = await _insert_article(db_session, "https://example.com/e")
    await save_article(db_session, user_id=user_id, article_id=article_id)

    removed = await unsave_article(db_session, user_id=user_id, article_id=article_id)

    assert removed is True
    assert await is_article_saved(db_session, user_id=user_id, article_id=article_id) is False


@pytest.mark.asyncio
async def test_unsave_article_returns_false_when_nothing_to_remove(db_session):
    removed = await unsave_article(db_session, user_id=1, article_id=999999)
    assert removed is False
