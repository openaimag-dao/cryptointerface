"""Persistence for AI news digests (`app/intelligence/llm/news_digest.py`)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.llm.news_digest import NewsDigestResult
from app.models.news_digest import NewsDigest


async def insert_news_digest(db: AsyncSession, result: NewsDigestResult) -> None:
    db.add(
        NewsDigest(
            topic=result.topic,
            summary=result.summary,
            highlights=result.highlights,
            article_count=result.article_count,
        )
    )
    await db.commit()


async def get_latest_news_digest(db: AsyncSession, topic: str) -> NewsDigest | None:
    # Order by id, not created_at: two digests generated in the same
    # scheduler cycle can land in the same millisecond, and id is the only
    # tiebreaker guaranteed to reflect insertion order.
    stmt = select(NewsDigest).where(NewsDigest.topic == topic).order_by(NewsDigest.id.desc()).limit(1)
    result = await db.execute(stmt)
    return result.scalars().first()
