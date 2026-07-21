"""Persistence for ingested news articles (`app/intelligence/news/`).

`insert_article` dedupes on `url` (`ON CONFLICT DO NOTHING`) — RSS feeds
re-serve the same articles on every poll, so this is idempotent and cheap
to call every cycle without accumulating duplicate rows.
"""

from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_engine.types import NewsSnapshot
from app.models.news import NewsArticle

# How far back a symbol/market-wide news snapshot looks for score_news()
# and the Sentiment Engine — recent enough that stale news doesn't keep
# moving the read, generous enough to have something on most watchlist
# symbols even with only 3 RSS sources.
SNAPSHOT_LOOKBACK_HOURS = 72
SNAPSHOT_LOOKBACK_LIMIT = 200


async def insert_article(
    db: AsyncSession,
    *,
    source: str,
    title: str,
    summary: str,
    url: str,
    published_at: int,
    language: str,
    symbols: list[str],
    impact_score: float,
    sentiment: str,
    category: str,
) -> bool:
    """Returns True if this was a genuinely new article (not a dupe)."""
    stmt = (
        pg_insert(NewsArticle)
        .values(
            source=source,
            title=title,
            summary=summary,
            url=url,
            published_at=published_at,
            language=language,
            symbols=symbols,
            impact_score=impact_score,
            sentiment=sentiment,
            category=category,
        )
        .on_conflict_do_nothing(index_elements=["url"])
        .returning(NewsArticle.id)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.first() is not None


async def get_latest_news(
    db: AsyncSession, limit: int = 30, symbol: str | None = None, category: str | None = None
) -> list[NewsArticle]:
    stmt = select(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(limit if symbol is None else 500)
    if category is not None:
        stmt = stmt.where(NewsArticle.category == category)
    result = await db.execute(stmt)
    articles = list(result.scalars().all())
    if symbol is not None:
        articles = [a for a in articles if symbol in a.symbols][:limit]
    return articles


async def search_news(db: AsyncSession, query: str, limit: int = 30) -> list[NewsArticle]:
    pattern = f"%{query}%"
    stmt = (
        select(NewsArticle)
        .where(or_(NewsArticle.title.ilike(pattern), NewsArticle.summary.ilike(pattern)))
        .order_by(NewsArticle.published_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_news_snapshot_for_symbol(db: AsyncSession, symbol: str) -> NewsSnapshot | None:
    """Builds the `ai_engine`-facing snapshot: recent articles that either
    mention this symbol directly, or are broad market-wide news (no
    specific symbol tag — e.g. a Fed/regulation story) — both move a
    symbol's news sentiment, just the untagged ones apply to everything.
    Returns None if there's no relevant news within the lookback window."""
    cutoff = int(datetime.now(UTC).timestamp()) - SNAPSHOT_LOOKBACK_HOURS * 3600
    stmt = (
        select(NewsArticle)
        .where(NewsArticle.published_at >= cutoff)
        .order_by(NewsArticle.published_at.desc())
        .limit(SNAPSHOT_LOOKBACK_LIMIT)
    )
    result = await db.execute(stmt)
    all_recent = result.scalars().all()
    relevant = [a for a in all_recent if not a.symbols or symbol in a.symbols]
    if not relevant:
        return None

    sentiment_values = {"BULLISH": 100.0, "NEUTRAL": 50.0, "BEARISH": 0.0}
    total_weight = sum(a.impact_score for a in relevant) or float(len(relevant))
    avg_sentiment_score = sum(sentiment_values[a.sentiment] * a.impact_score for a in relevant) / total_weight
    avg_impact = sum(a.impact_score for a in relevant) / len(relevant)

    return NewsSnapshot(
        article_count=len(relevant),
        avg_sentiment_score=avg_sentiment_score,
        avg_impact=avg_impact,
    )
