"""Admin API — editorial workflow moderation for the News Platform.

Every route here requires role="admin" (`get_current_admin_user`,
app/api/deps.py), enforced once for the whole router rather than per
endpoint. There is no self-service way to become an admin — see
backend/scripts/promote_to_admin.py for how the first one gets created.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user
from app.api.news import to_news_item
from app.database.session import get_db
from app.models.news import EDITORIAL_STATUSES
from app.schemas.admin import AdminNewsPage, AdminNewsUpdateRequest, EditorialStatusCounts
from app.schemas.news import NewsItem
from app.services.news_repository import (
    get_article_by_id,
    get_articles_by_editorial_status,
    get_editorial_status_counts,
)

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(get_current_admin_user)])


@router.get("/news", response_model=AdminNewsPage)
async def list_admin_news(
    status_filter: str = Query("PENDING_REVIEW", alias="status", description="One of EDITORIAL_STATUSES"),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> AdminNewsPage:
    if status_filter not in EDITORIAL_STATUSES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"Unknown status: {status_filter}. Must be one of {EDITORIAL_STATUSES}"
        )
    articles, total = await get_articles_by_editorial_status(db, status_filter, limit=limit, offset=offset)
    return AdminNewsPage(items=[to_news_item(a) for a in articles], total=total, limit=limit, offset=offset)


@router.get("/news/counts", response_model=EditorialStatusCounts)
async def get_news_counts(db: AsyncSession = Depends(get_db)) -> EditorialStatusCounts:
    counts = await get_editorial_status_counts(db)
    return EditorialStatusCounts(counts={s: counts.get(s, 0) for s in EDITORIAL_STATUSES})


@router.patch("/news/{article_id}", response_model=NewsItem)
async def update_admin_news(
    article_id: int, payload: AdminNewsUpdateRequest, db: AsyncSession = Depends(get_db)
) -> NewsItem:
    article = await get_article_by_id(db, article_id)
    if article is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No article with id {article_id}")

    if payload.editorial_status is not None and payload.editorial_status not in EDITORIAL_STATUSES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown status: {payload.editorial_status}")

    if payload.title is not None:
        article.title = payload.title
    if payload.summary is not None:
        article.summary = payload.summary
    if payload.category is not None:
        article.category = payload.category
    if payload.portal_topic is not None:
        article.portal_topic = payload.portal_topic
    if payload.editorial_status is not None:
        article.editorial_status = payload.editorial_status

    await db.commit()
    await db.refresh(article)
    return to_news_item(article)
