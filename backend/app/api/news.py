"""News Engine API — real (see app/intelligence/news/): RSS ingestion +
a deterministic keyword classifier, no LLM call per article.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.news import NewsArticle
from app.schemas.news import NewsItem, PortalNewsPage
from app.services.news_repository import get_article_by_id, get_latest_news, get_portal_news_page, search_news

router = APIRouter(prefix="/api/news", tags=["news"])

PORTAL_TOPICS = {"CRYPTO", "AI", "BLOCKCHAIN", "INNOVATION"}


def _to_news_item(article: NewsArticle) -> NewsItem:
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
    return [_to_news_item(a) for a in articles]


@router.get("/latest", response_model=list[NewsItem])
async def latest_news(limit: int = Query(10, ge=1, le=50), db: AsyncSession = Depends(get_db)) -> list[NewsItem]:
    articles = await get_latest_news(db, limit=limit)
    return [_to_news_item(a) for a in articles]


@router.get("/search", response_model=list[NewsItem])
async def search(
    q: str = Query(..., min_length=1), limit: int = Query(30, ge=1, le=100), db: AsyncSession = Depends(get_db)
) -> list[NewsItem]:
    articles = await search_news(db, q, limit=limit)
    return [_to_news_item(a) for a in articles]


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
    return PortalNewsPage(items=[_to_news_item(a) for a in articles], total=total, limit=limit, offset=offset)


@router.get("/{article_id}", response_model=NewsItem)
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)) -> NewsItem:
    article = await get_article_by_id(db, article_id)
    if article is None:
        raise HTTPException(status_code=404, detail=f"No article with id {article_id}")
    return _to_news_item(article)
