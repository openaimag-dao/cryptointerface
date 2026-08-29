"""Persistence for `NewsSource` — the admin-manageable, DB-backed source
registry the ingestion pipeline reads from (see app/models/news_source.py
for why this exists alongside the static `NEWS_SOURCES` list)."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.news.sources import NEWS_SOURCES
from app.models.news_fetch_log import NewsFetchLog
from app.models.news_source import NewsSource


async def seed_default_sources(db: AsyncSession) -> None:
    """Idempotent: inserts each static NEWS_SOURCES entry as a row on
    `source_key` if it isn't already there. Never overwrites an existing
    row — once a source exists in the DB, an admin owns its settings."""
    for source_def in NEWS_SOURCES:
        stmt = (
            pg_insert(NewsSource)
            .values(
                source_key=source_def.id,
                name=source_def.name,
                rss_url=source_def.rss_url,
                language=source_def.language,
                default_topic=source_def.default_topic,
            )
            .on_conflict_do_nothing(index_elements=["source_key"])
        )
        await db.execute(stmt)
    await db.commit()


async def get_enabled_sources(db: AsyncSession) -> list[NewsSource]:
    stmt = select(NewsSource).where(NewsSource.enabled.is_(True))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_all_sources(db: AsyncSession) -> list[NewsSource]:
    stmt = select(NewsSource).order_by(NewsSource.name)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_source_by_id(db: AsyncSession, source_id: int) -> NewsSource | None:
    return await db.get(NewsSource, source_id)


async def record_fetch_result(
    db: AsyncSession,
    source: NewsSource,
    *,
    status: str,
    articles_found: int,
    articles_new: int,
    duration_ms: int,
    error_message: str | None = None,
) -> None:
    """Updates the source's rolling health fields and appends one
    NewsFetchLog row — called once per source per poll cycle regardless
    of outcome, so a persistently-failing source is visible in the admin
    monitoring view (section 29) rather than silently going quiet."""
    source.last_fetched_at = datetime.now(UTC)
    source.last_status = status
    source.last_error = error_message
    source.articles_imported_count += articles_new
    db.add(
        NewsFetchLog(
            source_id=source.id,
            status=status,
            articles_found=articles_found,
            articles_new=articles_new,
            error_message=error_message,
            duration_ms=duration_ms,
        )
    )
    await db.commit()
