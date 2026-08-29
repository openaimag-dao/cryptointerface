from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import NewsArticle
from app.models.saved_article import SavedArticle


async def save_article(db: AsyncSession, *, user_id: int, article_id: int) -> bool:
    """Returns True if this was a new bookmark (idempotent — saving an
    already-saved article is a no-op, not an error)."""
    stmt = (
        pg_insert(SavedArticle)
        .values(user_id=user_id, article_id=article_id)
        .on_conflict_do_nothing(index_elements=["user_id", "article_id"])
        .returning(SavedArticle.id)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.first() is not None


async def unsave_article(db: AsyncSession, *, user_id: int, article_id: int) -> bool:
    stmt = select(SavedArticle).where(SavedArticle.user_id == user_id, SavedArticle.article_id == article_id)
    result = await db.execute(stmt)
    saved = result.scalars().first()
    if saved is None:
        return False
    await db.delete(saved)
    await db.commit()
    return True


async def list_saved_articles(db: AsyncSession, user_id: int) -> list[NewsArticle]:
    stmt = (
        select(NewsArticle)
        .join(SavedArticle, SavedArticle.article_id == NewsArticle.id)
        .where(SavedArticle.user_id == user_id)
        .order_by(SavedArticle.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def is_article_saved(db: AsyncSession, *, user_id: int, article_id: int) -> bool:
    stmt = select(SavedArticle.id).where(SavedArticle.user_id == user_id, SavedArticle.article_id == article_id)
    result = await db.execute(stmt)
    return result.first() is not None
