"""Persistence for `NewsEvent` deduplication grouping (see
app/intelligence/news/dedup.py for the matching logic itself)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.news.dedup import TIME_WINDOW_HOURS, compute_importance_score, find_best_candidate
from app.models.news import NewsArticle
from app.models.news_event import NewsEvent


async def get_dedup_candidates(db: AsyncSession, article: NewsArticle) -> list[NewsArticle]:
    """Recent articles in the same portal topic within the dedup time
    window — the pool `find_best_candidate` matches `article` against."""
    cutoff = article.published_at - TIME_WINDOW_HOURS * 3600
    horizon = article.published_at + TIME_WINDOW_HOURS * 3600
    stmt = select(NewsArticle).where(
        NewsArticle.portal_topic == article.portal_topic,
        NewsArticle.published_at >= cutoff,
        NewsArticle.published_at <= horizon,
        NewsArticle.id != article.id,
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def assign_to_event(db: AsyncSession, article: NewsArticle) -> NewsEvent | None:
    """Finds the best-matching recent article and either joins its
    existing NewsEvent or creates a new one covering both. Returns None
    (article stays ungrouped — a "solo" story) if nothing matches closely
    enough. Idempotent: an article that's already assigned to an event is
    left alone."""
    if article.news_event_id is not None:
        return await db.get(NewsEvent, article.news_event_id)

    candidates = await get_dedup_candidates(db, article)
    match = find_best_candidate(article, candidates)
    if match is None:
        return None

    if match.news_event_id is not None:
        event = await db.get(NewsEvent, match.news_event_id)
        assert event is not None  # FK guarantees this
        article.news_event_id = event.id
        await db.flush()
        # Recompute now that a new source corroborates the story — more
        # independent coverage should be able to raise importance even if
        # this article's own impact_score is lower than the event's peak.
        event_articles = await get_event_articles(db, event.id)
        event.importance_score = compute_importance_score([a.impact_score for a in event_articles])
        await db.commit()
        return event

    # Neither article is grouped yet — start a new event, anchored on
    # whichever of the two published first.
    primary, secondary = (article, match) if article.published_at <= match.published_at else (match, article)
    event = NewsEvent(
        title=primary.title,
        portal_topic=primary.portal_topic,
        importance_score=compute_importance_score([primary.impact_score, secondary.impact_score]),
    )
    db.add(event)
    await db.flush()  # need event.id before it can be a FK target below
    event.primary_article_id = primary.id
    primary.news_event_id = event.id
    secondary.news_event_id = event.id
    await db.commit()
    return event


async def get_event_articles(db: AsyncSession, event_id: int) -> list[NewsArticle]:
    stmt = (
        select(NewsArticle).where(NewsArticle.news_event_id == event_id).order_by(NewsArticle.published_at.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_event_by_id(db: AsyncSession, event_id: int) -> NewsEvent | None:
    return await db.get(NewsEvent, event_id)
