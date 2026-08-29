"""News Engine API — real (see app/intelligence/news/): RSS ingestion +
a deterministic keyword classifier, no LLM call per article.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.news import NewsArticle
from app.schemas.news import NewsEventOut, NewsItem, PortalNewsPage
from app.schemas.news_digest import NewsDigestOut
from app.services.news_digest_repository import get_latest_news_digest
from app.services.news_event_repository import get_event_articles, get_event_by_id
from app.services.news_repository import (
    get_article_by_id,
    get_latest_news,
    get_portal_news_page,
    get_trending_news,
    search_news,
)

router = APIRouter(prefix="/api/news", tags=["news"])

PORTAL_TOPICS = {"CRYPTO", "AI", "BLOCKCHAIN", "INNOVATION"}


def to_news_item(article: NewsArticle) -> NewsItem:
    return NewsItem(
        id=str(article.id),
        source=article.source,
        title=article.title,
        summary=article.summary,
        published_at=datetime.fromtimestamp(article.published_at, tz=UTC).isoformat(),
        language=article.language,
        symbols=article.symbols,
        url=article.url,
        impact_score=round(article.impact_score, 1),
        sentiment=article.sentiment,
        category=article.category,
        portal_topic=article.portal_topic,
        ai_summary=article.ai_summary,
    )


@router.get("", response_model=list[NewsItem])
async def list_news(
    limit: int = Query(30, ge=1, le=200),
    symbol: str | None = Query(default=None, description="Base asset ticker, e.g. BTC"),
    category: str | None = Query(default=None),
    topic: str | None = Query(default=None, description="Portal topic: CRYPTO, AI, BLOCKCHAIN, or INNOVATION"),
    db: AsyncSession = Depends(get_db),
) -> list[NewsItem]:
    symbol = symbol.upper() if symbol else None
    articles = await get_latest_news(db, limit=limit, symbol=symbol, category=category, topic=topic)
    return [to_news_item(a) for a in articles]


@router.get("/latest", response_model=list[NewsItem])
async def latest_news(limit: int = Query(10, ge=1, le=50), db: AsyncSession = Depends(get_db)) -> list[NewsItem]:
    articles = await get_latest_news(db, limit=limit)
    return [to_news_item(a) for a in articles]


@router.get("/search", response_model=PortalNewsPage)
async def search(
    q: str = Query(..., min_length=1),
    topic: str | None = Query(default=None, description="CRYPTO, AI, BLOCKCHAIN, or INNOVATION"),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> PortalNewsPage:
    """Real Postgres full-text search (news_repository.py::search_news),
    relevance-ranked, PUBLISHED-only. `topic` filters to one portal
    section the same way `/portal` does."""
    if topic is not None and topic not in PORTAL_TOPICS:
        raise HTTPException(status_code=400, detail=f"Unknown topic: {topic}. Must be one of {sorted(PORTAL_TOPICS)}")
    articles, total = await search_news(db, q, topic=topic, limit=limit, offset=offset)
    return PortalNewsPage(items=[to_news_item(a) for a in articles], total=total, limit=limit, offset=offset)


@router.get("/trending", response_model=list[NewsItem])
async def trending_news(
    topic: str | None = Query(default=None, description="CRYPTO, AI, BLOCKCHAIN, or INNOVATION"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> list[NewsItem]:
    """Real trending ranking (news_repository.py::get_trending_news) — the
    same deterministic importance_score the dedup engine and admin panel
    already compute, over the last 48h, deduplicated to one slot per
    NewsEvent. No fabricated view/click counters."""
    if topic is not None and topic not in PORTAL_TOPICS:
        raise HTTPException(status_code=400, detail=f"Unknown topic: {topic}. Must be one of {sorted(PORTAL_TOPICS)}")
    articles = await get_trending_news(db, topic=topic, limit=limit)
    return [to_news_item(a) for a in articles]


@router.get("/portal", response_model=PortalNewsPage)
async def portal_news(
    topic: str | None = Query(default=None, description="CRYPTO, AI, BLOCKCHAIN, or INNOVATION"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> PortalNewsPage:
    """Real DB-level pagination for the public news portal — distinct from
    `list_news`'s Python-side symbol filter, which isn't paginated."""
    if topic is not None and topic not in PORTAL_TOPICS:
        raise HTTPException(status_code=400, detail=f"Unknown topic: {topic}. Must be one of {sorted(PORTAL_TOPICS)}")
    articles, total = await get_portal_news_page(db, topic=topic, limit=limit, offset=offset)
    return PortalNewsPage(items=[to_news_item(a) for a in articles], total=total, limit=limit, offset=offset)


@router.get("/digest", response_model=NewsDigestOut)
async def get_news_digest(
    topic: str = Query(..., description="CRYPTO, AI, BLOCKCHAIN, or INNOVATION"),
    db: AsyncSession = Depends(get_db),
) -> NewsDigestOut:
    """Reads the latest AI-narrated digest generated on a schedule by
    `run_news_digest_refresh` — never calls Claude inline, so this stays
    cheap for a public portal page to poll. See
    app/intelligence/llm/news_digest.py."""
    if topic not in PORTAL_TOPICS:
        raise HTTPException(status_code=400, detail=f"Unknown topic: {topic}. Must be one of {sorted(PORTAL_TOPICS)}")
    digest = await get_latest_news_digest(db, topic)
    if digest is None:
        raise HTTPException(status_code=404, detail=f"No digest generated yet for {topic}")
    return NewsDigestOut(
        topic=digest.topic,
        summary=digest.summary,
        highlights=digest.highlights,
        article_count=digest.article_count,
        generated_at=digest.created_at.isoformat(),
    )


@router.get("/events/{event_id}", response_model=NewsEventOut)
async def get_news_event(event_id: int, db: AsyncSession = Depends(get_db)) -> NewsEventOut:
    """Multi-source coverage of one deduplicated event (see
    app/intelligence/news/dedup.py) — the grouped articles, earliest
    first."""
    event = await get_event_by_id(db, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail=f"No event with id {event_id}")
    articles = await get_event_articles(db, event_id)
    return NewsEventOut(
        id=str(event.id),
        title=event.title,
        portal_topic=event.portal_topic,
        importance_score=round(event.importance_score, 1),
        articles=[to_news_item(a) for a in articles],
    )


@router.get("/{article_id}", response_model=NewsItem)
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)) -> NewsItem:
    article = await get_article_by_id(db, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail=f"No article with id {article_id}")
    return to_news_item(article)
