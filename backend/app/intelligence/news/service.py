"""Fetches every enabled RSS source (from the DB — see
app/models/news_source.py), classifies each article with the
deterministic classifier, and persists it (deduped on URL). Called by the
scheduler on `NEWS_POLL_INTERVAL_SECONDS` — one source failing never
blocks the others (see `fetcher.py`), and every source's outcome is
logged via `news_source_repository.record_fetch_result` for the admin
monitoring view.
"""

import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.intelligence.news.classifier import classify, classify_portal_topic
from app.intelligence.news.fetcher import fetch_source
from app.services.news_event_repository import assign_to_event
from app.services.news_repository import get_article_by_url, insert_article
from app.services.news_source_repository import get_enabled_sources, record_fetch_result

logger = get_logger(__name__)


async def fetch_and_persist_news(db: AsyncSession) -> int:
    """Returns the number of genuinely new (non-duplicate) articles
    persisted this cycle."""
    new_count = 0
    sources = await get_enabled_sources(db)

    for source in sources:
        started = time.monotonic()
        editorial_status = "PUBLISHED" if source.auto_publish else "PENDING_REVIEW"
        try:
            entries = await fetch_source(source.to_source_def())
        except Exception as exc:  # noqa: BLE001 — one dead source must not stop the others
            await record_fetch_result(
                db, source, status="ERROR", articles_found=0, articles_new=0,
                duration_ms=int((time.monotonic() - started) * 1000), error_message=str(exc),
            )
            logger.warning("news_source_poll_failed", extra={"source": source.source_key, "error": str(exc)})
            continue

        source_new_count = 0
        for entry in entries:
            classification = classify(entry.title, entry.summary)
            portal_topic = classify_portal_topic(f"{entry.title} {entry.summary}", source.default_topic)
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
                portal_topic=portal_topic,
                editorial_status=editorial_status,
                image_url=entry.image_url,
            )
            if inserted:
                source_new_count += 1
                # Only newly-inserted articles need dedup — one that already
                # existed (ON CONFLICT DO NOTHING) was already processed on
                # an earlier poll cycle.
                new_article = await get_article_by_url(db, entry.url)
                if new_article is not None:
                    await assign_to_event(db, new_article)

        new_count += source_new_count
        await record_fetch_result(
            db,
            source,
            status="SUCCESS",
            articles_found=len(entries),
            articles_new=source_new_count,
            duration_ms=int((time.monotonic() - started) * 1000),
        )

    logger.info("news_poll_cycle_complete", extra={"new_articles": new_count, "sources": len(sources)})
    return new_count
