"""News Engine API — real (see app/intelligence/news/): RSS ingestion +
a deterministic keyword classifier, no LLM call per article.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.news import NewsArticle
from app.schemas.news import NewsItem
from app.services.news_repository import get_latest_news, search_news

router = APIRouter(prefix="/api/news", tags=["news"])


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
    )


@router.get("", response_model=list[NewsItem])
async def list_news(
    limit: int = Query(30, ge=1, le=200),
    symbol: str | None = Query(default=None, description="Base asset ticker, e.g. BTC"),
    category: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[NewsItem]:
    symbol = symbol.upper() if symbol else None
    articles = await get_latest_news(db, limit=limit, symbol=symbol, category=category)
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
