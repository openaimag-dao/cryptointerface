"""Persistence for `Entity`/`ArticleEntity` — the named things (companies,
people, cryptocurrencies, protocols, countries, technologies) AI News
Processing extracts per article (see app/intelligence/llm/news_processing.py).
"""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.llm.news_processing import ExtractedEntity
from app.models.article_associations import ArticleEntity
from app.models.entity import Entity
from app.utils.slug import simple_slugify


async def get_or_create_entity(db: AsyncSession, name: str, entity_type: str) -> Entity:
    """Upserts on `slug`, so "Bitcoin" mentioned in 50 different articles
    resolves to the same row every time rather than 50 duplicates."""
    slug = simple_slugify(name)
    stmt = (
        pg_insert(Entity)
        .values(name=name, slug=slug, entity_type=entity_type)
        .on_conflict_do_nothing(index_elements=["slug"])
    )
    await db.execute(stmt)
    await db.commit()

    result = await db.execute(select(Entity).where(Entity.slug == slug))
    return result.scalars().one()


async def link_article_entities(db: AsyncSession, article_id: int, entities: list[ExtractedEntity]) -> None:
    """Idempotent — re-processing the same article (shouldn't happen once
    `ai_summary` is set, but defensively) never creates duplicate links."""
    for extracted in entities:
        entity = await get_or_create_entity(db, extracted.name, extracted.entity_type)
        stmt = (
            pg_insert(ArticleEntity)
            .values(article_id=article_id, entity_id=entity.id)
            .on_conflict_do_nothing(index_elements=["article_id", "entity_id"])
        )
        await db.execute(stmt)
    await db.commit()


async def get_entities_for_article(db: AsyncSession, article_id: int) -> list[Entity]:
    stmt = select(Entity).join(ArticleEntity, ArticleEntity.entity_id == Entity.id).where(
        ArticleEntity.article_id == article_id
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
