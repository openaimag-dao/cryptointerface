from datetime import UTC, datetime

import pytest

from app.intelligence.llm.news_processing import ExtractedEntity
from app.services.entity_repository import get_entities_for_article, get_or_create_entity, link_article_entities
from app.services.news_repository import insert_article


async def _insert_article(db_session, url: str = "https://example.com/a") -> int:
    from sqlalchemy import select

    from app.models.news import NewsArticle

    await insert_article(
        db_session,
        source="Test",
        title="OpenAI launches new AI model",
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


@pytest.mark.asyncio
async def test_get_or_create_entity_creates_a_new_entity(db_session):
    entity = await get_or_create_entity(db_session, "OpenAI", "COMPANY")

    assert entity.name == "OpenAI"
    assert entity.entity_type == "COMPANY"
    assert entity.slug == "openai"


@pytest.mark.asyncio
async def test_get_or_create_entity_is_idempotent_by_slug(db_session):
    first = await get_or_create_entity(db_session, "Bitcoin", "CRYPTOCURRENCY")
    second = await get_or_create_entity(db_session, "bitcoin", "CRYPTOCURRENCY")

    assert first.id == second.id


@pytest.mark.asyncio
async def test_link_article_entities_creates_links(db_session):
    article_id = await _insert_article(db_session)

    await link_article_entities(
        db_session, article_id, [ExtractedEntity(name="OpenAI", entity_type="COMPANY")]
    )

    entities = await get_entities_for_article(db_session, article_id)
    assert len(entities) == 1
    assert entities[0].name == "OpenAI"


@pytest.mark.asyncio
async def test_link_article_entities_is_idempotent(db_session):
    article_id = await _insert_article(db_session)
    entity_list = [ExtractedEntity(name="OpenAI", entity_type="COMPANY")]

    await link_article_entities(db_session, article_id, entity_list)
    await link_article_entities(db_session, article_id, entity_list)

    entities = await get_entities_for_article(db_session, article_id)
    assert len(entities) == 1


@pytest.mark.asyncio
async def test_link_article_entities_links_multiple_distinct_entities(db_session):
    article_id = await _insert_article(db_session)

    await link_article_entities(
        db_session,
        article_id,
        [
            ExtractedEntity(name="OpenAI", entity_type="COMPANY"),
            ExtractedEntity(name="Sam Altman", entity_type="PERSON"),
        ],
    )

    entities = await get_entities_for_article(db_session, article_id)
    assert {e.name for e in entities} == {"OpenAI", "Sam Altman"}


@pytest.mark.asyncio
async def test_get_entities_for_article_returns_empty_list_when_none_linked(db_session):
    article_id = await _insert_article(db_session)
    assert await get_entities_for_article(db_session, article_id) == []
