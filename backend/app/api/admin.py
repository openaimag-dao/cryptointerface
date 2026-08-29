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
from app.schemas.admin import (
    AdminFetchLogOut,
    AdminNewsPage,
    AdminNewsUpdateRequest,
    AdminSourceOut,
    AdminSourceUpdateRequest,
    EditorialStatusCounts,
)
from app.schemas.news import NewsItem
from app.services.news_repository import (
    get_article_by_id,
    get_articles_by_editorial_status,
    get_editorial_status_counts,
)
from app.services.news_source_repository import (
    get_all_sources,
    get_recent_fetch_logs,
    get_source_by_id,
    update_source,
)

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(get_current_admin_user)])


def _to_admin_source(source) -> AdminSourceOut:
    return AdminSourceOut(
        id=str(source.id),
        source_key=source.source_key,
        name=source.name,
        rss_url=source.rss_url,
        language=source.language,
        default_topic=source.default_topic,
        trust_score=source.trust_score,
        enabled=source.enabled,
        auto_publish=source.auto_publish,
        last_fetched_at=source.last_fetched_at.isoformat() if source.last_fetched_at else None,
        last_status=source.last_status,
        last_error=source.last_error,
        articles_imported_count=source.articles_imported_count,
    )


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


@router.get("/sources", response_model=list[AdminSourceOut])
async def list_admin_sources(db: AsyncSession = Depends(get_db)) -> list[AdminSourceOut]:
    """DB-backed source registry (app/models/news_source.py) — the
    ingestion pipeline's source of truth. Toggling `enabled`/
    `auto_publish` here takes effect on the next poll cycle, no deploy."""
    sources = await get_all_sources(db)
    return [_to_admin_source(s) for s in sources]


@router.patch("/sources/{source_id}", response_model=AdminSourceOut)
async def update_admin_source(
    source_id: int, payload: AdminSourceUpdateRequest, db: AsyncSession = Depends(get_db)
) -> AdminSourceOut:
    source = await get_source_by_id(db, source_id)
    if source is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No source with id {source_id}")

    fields = payload.model_dump(exclude_unset=True)
    updated = await update_source(db, source, fields)
    return _to_admin_source(updated)


@router.get("/fetch-logs", response_model=list[AdminFetchLogOut])
async def list_admin_fetch_logs(
    source_id: int | None = Query(default=None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[AdminFetchLogOut]:
    """Ingestion monitoring: recent RSS poll attempts, newest first — a
    persistently-failing source is visible here, not silently going
    quiet. Joins each log's source name in Python (small N, avoids a
    fragile hand-written SQL join for a low-traffic admin-only view)."""
    logs = await get_recent_fetch_logs(db, source_id=source_id, limit=limit)
    source_ids = {log.source_id for log in logs}
    sources = {sid: await get_source_by_id(db, sid) for sid in source_ids}
    return [
        AdminFetchLogOut(
            id=str(log.id),
            source_id=str(log.source_id),
            source_name=sources[log.source_id].name if sources.get(log.source_id) else "Unknown source",
            status=log.status,
            articles_found=log.articles_found,
            articles_new=log.articles_new,
            error_message=log.error_message,
            duration_ms=log.duration_ms,
            created_at=log.created_at.isoformat(),
        )
        for log in logs
    ]
