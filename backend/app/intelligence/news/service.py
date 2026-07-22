"""Fetches every registered RSS source, classifies each article with the
deterministic classifier, and persists it (deduped on URL). Called by the
scheduler on `NEWS_POLL_INTERVAL_SECONDS` — one source failing never
blocks the others (see `fetcher.py`).
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.intelligence.news.classifier import classify
from app.intelligence.news.fetcher import fetch_source
from app.intelligence.news.sources import NEWS_SOURCES
from app.services.news_repository import insert_article

logger = get_logger(__name__)


async def fetch_and_persist_news(db: AsyncSession) -> int:
    """Returns the number of genuinely new (non-duplicate) articles
    persisted this cycle."""
    new_count = 0
    for source in NEWS_SOURCES:
        entries = await fetch_source(source)
        for entry in entries:
            classification = classify(entry.title, entry.summary)
            inserted = await insert_article(
                db,
                source=entry.source,
                title=entry.title,
                summary=entry.summary,
                url=entry.url,
                published_at=entry.published_at,
                language=entry.language,
                symbols=classification.symbols,
                impact_score=classification.impact_score,
                sentiment=classification.sentiment,
                category=classification.category,
            )
            if inserted:
                new_count += 1

    logger.info("news_poll_cycle_complete", extra={"new_articles": new_count, "sources": len(NEWS_SOURCES)})
    return new_count
