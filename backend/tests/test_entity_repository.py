from datetime import UTC, datetime

import pytest

from app.intelligence.llm.news_processing import ExtractedEntity
from app.models.entity import Entity
from app.services.entity_repository import (
    get_articles_for_entity,
    get_entities_for_article,
    get_entities_for_articles,
    get_entity_by_slug,
    get_or_create_entity,
    link_article_entities,
)
from app.services.news_repository import insert_article


async def _insert_article(
    db_session, url: str = "https://example.com/a", editorial_status: str = "PUBLISHED"
) -> int:
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
        editorial_status=editorial_status,
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
async def test_get_or_create_entity_capitalizes_a_lowercase_llm_extraction(db_session):
    entity = await get_or_create_entity(db_session, "bitcoin", "CRYPTOCURRENCY")

    assert entity.name == "Bitcoin"


@pytest.mark.asyncio
async def test_get_or_create_entity_preserves_internal_casing(db_session):
    entity = await get_or_create_entity(db_session, "OpenAI", "COMPANY")

    assert entity.name == "OpenAI"


@pytest.mark.asyncio
async def test_get_or_create_entity_heals_an_existing_rows_casing(db_session):
    # Simulates data created before this normalization existed (or by a
    # slug collision that lost the casing race) — bypasses the repository
    # function entirely so the row starts out genuinely lowercase.
    stale = Entity(name="bitcoin", slug="bitcoin", entity_type="CRYPTOCURRENCY")
    db_session.add(stale)
    await db_session.commit()

    healed = await get_or_create_entity(db_session, "Bitcoin", "CRYPTOCURRENCY")

    assert healed.id == stale.id
    assert healed.name == "Bitcoin"


@pytest.mark.asyncio
async def test_get_or_create_entity_does_not_overwrite_entity_type_on_conflict(db_session):
    first = await get_or_create_entity(db_session, "Bitcoin", "CRYPTOCURRENCY")

    # A later, wrong classification of the same slug must never clobber
    # the entity_type an earlier, correct extraction already set.
    second = await get_or_create_entity(db_session, "Bitcoin", "COMPANY")

    assert second.id == first.id
    assert second.entity_type == "CRYPTOCURRENCY"


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


@pytest.mark.asyncio
async def test_get_entities_for_articles_bulk_lookup(db_session):
    article_a = await _insert_article(db_session, url="https://example.com/a")
    article_b = await _insert_article(db_session, url="https://example.com/b")
    await link_article_entities(db_session, article_a, [ExtractedEntity(name="OpenAI", entity_type="COMPANY")])
    await link_article_entities(db_session, article_b, [ExtractedEntity(name="Bitcoin", entity_type="CRYPTOCURRENCY")])

    by_article = await get_entities_for_articles(db_session, [article_a, article_b])

    assert {e.name for e in by_article[article_a]} == {"OpenAI"}
    assert {e.name for e in by_article[article_b]} == {"Bitcoin"}


@pytest.mark.asyncio
async def test_get_entities_for_articles_returns_empty_dict_for_empty_input(db_session):
    assert await get_entities_for_articles(db_session, []) == {}


@pytest.mark.asyncio
async def test_get_entity_by_slug_finds_existing_entity(db_session):
    created = await get_or_create_entity(db_session, "Bitcoin", "CRYPTOCURRENCY")

    found = await get_entity_by_slug(db_session, "bitcoin")

    assert found is not None
    assert found.id == created.id


@pytest.mark.asyncio
async def test_get_entity_by_slug_returns_none_for_unknown_slug(db_session):
    assert await get_entity_by_slug(db_session, "does-not-exist") is None


@pytest.mark.asyncio
async def test_get_articles_for_entity_returns_published_only_newest_first(db_session):
    entity = await get_or_create_entity(db_session, "Bitcoin", "CRYPTOCURRENCY")
    published = await _insert_article(db_session, url="https://example.com/published")
    pending = await _insert_article(db_session, url="https://example.com/pending", editorial_status="PENDING_REVIEW")
    for article_id in (published, pending):
        await link_article_entities(db_session, article_id, [ExtractedEntity(name="Bitcoin", entity_type="CRYPTOCURRENCY")])

    articles, total = await get_articles_for_entity(db_session, entity.id)

    assert total == 1
    assert [a.id for a in articles] == [published]


@pytest.mark.asyncio
async def test_get_articles_for_entity_paginates(db_session):
    entity = await get_or_create_entity(db_session, "Bitcoin", "CRYPTOCURRENCY")
    for i in range(3):
        article_id = await _insert_article(db_session, url=f"https://example.com/{i}")
        await link_article_entities(db_session, article_id, [ExtractedEntity(name="Bitcoin", entity_type="CRYPTOCURRENCY")])

    first_page, total = await get_articles_for_entity(db_session, entity.id, limit=2, offset=0)
    second_page, _ = await get_articles_for_entity(db_session, entity.id, limit=2, offset=2)

    assert total == 3
    assert len(first_page) == 2
    assert len(second_page) == 1
