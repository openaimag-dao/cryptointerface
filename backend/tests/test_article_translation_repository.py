from datetime import UTC, datetime

import pytest

from app.services.article_translation_repository import (
    get_articles_missing_translation,
    get_translations_for_articles,
    upsert_translation,
)
from app.services.news_repository import insert_article


async def _insert(db_session, *, url: str, editorial_status: str = "PUBLISHED") -> int:
    from sqlalchemy import select

    from app.models.news import NewsArticle

    await insert_article(
        db_session,
        source="Test Source",
        title="Title",
        summary="Summary",
        url=url,
        published_at=int(datetime.now(UTC).timestamp()),
        language="en",
        symbols=[],
        impact_score=50.0,
        sentiment="NEUTRAL",
        category="Market",
        editorial_status=editorial_status,
    )
    result = await db_session.execute(select(NewsArticle).where(NewsArticle.url == url))
    return result.scalars().one().id


@pytest.mark.asyncio
async def test_upsert_translation_creates_a_row(db_session):
    article_id = await _insert(db_session, url="https://example.com/a")

    translation = await upsert_translation(db_session, article_id, "ru", "Заголовок", "Описание")

    assert translation.article_id == article_id
    assert translation.language == "ru"
    assert translation.title == "Заголовок"


@pytest.mark.asyncio
async def test_upsert_translation_replaces_an_existing_row(db_session):
    article_id = await _insert(db_session, url="https://example.com/b")
    await upsert_translation(db_session, article_id, "ru", "Old Title", "Old Summary")

    updated = await upsert_translation(db_session, article_id, "ru", "New Title", "New Summary")

    assert updated.title == "New Title"
    translations = await get_translations_for_articles(db_session, [article_id], "ru")
    assert len(translations) == 1
    assert translations[article_id].title == "New Title"


@pytest.mark.asyncio
async def test_get_translations_for_articles_scopes_by_language(db_session):
    article_id = await _insert(db_session, url="https://example.com/c")
    await upsert_translation(db_session, article_id, "ru", "RU Title", "RU Summary")
    await upsert_translation(db_session, article_id, "kk", "KK Title", "KK Summary")

    ru_only = await get_translations_for_articles(db_session, [article_id], "ru")

    assert len(ru_only) == 1
    assert ru_only[article_id].language == "ru"


@pytest.mark.asyncio
async def test_get_translations_for_articles_returns_empty_dict_for_no_ids(db_session):
    result = await get_translations_for_articles(db_session, [], "ru")
    assert result == {}


@pytest.mark.asyncio
async def test_get_articles_missing_translation_excludes_already_translated(db_session):
    translated_id = await _insert(db_session, url="https://example.com/translated")
    untranslated_id = await _insert(db_session, url="https://example.com/untranslated")
    await upsert_translation(db_session, translated_id, "ru", "Title", "Summary")

    missing = await get_articles_missing_translation(db_session, "ru")

    missing_ids = {a.id for a in missing}
    assert untranslated_id in missing_ids
    assert translated_id not in missing_ids


@pytest.mark.asyncio
async def test_get_articles_missing_translation_excludes_non_published(db_session):
    await _insert(db_session, url="https://example.com/pending", editorial_status="PENDING_REVIEW")
    published_id = await _insert(db_session, url="https://example.com/published")

    missing = await get_articles_missing_translation(db_session, "ru")

    missing_ids = {a.id for a in missing}
    assert missing_ids == {published_id}
