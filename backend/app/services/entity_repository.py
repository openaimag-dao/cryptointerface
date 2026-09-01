"""Persistence for `Entity`/`ArticleEntity` — the named things (companies,
people, cryptocurrencies, protocols, countries, technologies) AI News
Processing extracts per article (see app/intelligence/llm/news_processing.py).
"""

from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.llm.news_processing import ExtractedEntity
from app.models.article_associations import ArticleEntity
from app.models.entity import Entity
from app.models.news import NewsArticle
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


async def get_entities_for_articles(db: AsyncSession, article_ids: list[int]) -> dict[int, list[Entity]]:
    """Bulk lookup for a page of articles — one query instead of N, keyed
    by article_id — same shape as get_translations_for_articles
    (article_translation_repository.py)."""
    if not article_ids:
        return {}
    stmt = (
        select(ArticleEntity.article_id, Entity)
        .join(Entity, Entity.id == ArticleEntity.entity_id)
        .where(ArticleEntity.article_id.in_(article_ids))
    )
    result = await db.execute(stmt)
    by_article: dict[int, list[Entity]] = defaultdict(list)
    for article_id, entity in result.all():
        by_article[article_id].append(entity)
    return dict(by_article)


async def get_entity_by_slug(db: AsyncSession, slug: str) -> Entity | None:
    result = await db.execute(select(Entity).where(Entity.slug == slug))
    return result.scalars().one_or_none()


async def get_articles_for_entity(
    db: AsyncSession, entity_id: int, limit: int = 20, offset: int = 0
) -> tuple[list[NewsArticle], int]:
    """Paginated PUBLISHED-only listing for one AI-extracted entity's tag
    archive page — real DB-level pagination, same shape as
    news_repository.py::get_portal_news_page."""
    base_stmt = (
        select(NewsArticle)
        .join(ArticleEntity, ArticleEntity.article_id == NewsArticle.id)
        .where(ArticleEntity.entity_id == entity_id, NewsArticle.editorial_status == "PUBLISHED")
    )
    count_stmt = (
        select(func.count())
        .select_from(NewsArticle)
        .join(ArticleEntity, ArticleEntity.article_id == NewsArticle.id)
        .where(ArticleEntity.entity_id == entity_id, NewsArticle.editorial_status == "PUBLISHED")
    )
    total = (await db.execute(count_stmt)).scalar_one()
    stmt = base_stmt.order_by(NewsArticle.published_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all()), total
