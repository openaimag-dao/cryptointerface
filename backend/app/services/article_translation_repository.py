"""Persistence for `ArticleTranslation` (see app/models/article_translation.py
for why this is a separate table rather than extra columns on NewsArticle
or duplicated NewsArticle rows per language)."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article_translation import ArticleTranslation
from app.models.news import NewsArticle


async def upsert_translation(
    db: AsyncSession, article_id: int, language: str, title: str, summary: str
) -> ArticleTranslation:
    """Insert-or-update on (article_id, language) — a re-run of the
    translation scheduler for an article that already has one (e.g. after
    an editor edits the English title/summary) replaces it rather than
    accumulating duplicate rows."""
    stmt = (
        pg_insert(ArticleTranslation)
        .values(article_id=article_id, language=language, title=title, summary=summary)
        .on_conflict_do_update(
            index_elements=["article_id", "language"],
            set_={"title": title, "summary": summary},
        )
        .returning(ArticleTranslation)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalar_one()


async def get_translations_for_articles(
    db: AsyncSession, article_ids: list[int], language: str
) -> dict[int, ArticleTranslation]:
    """Bulk lookup for a page of articles — one query instead of N, keyed
    by article_id so callers can do a dict lookup per item while building
    a response page."""
    if not article_ids:
        return {}
    stmt = select(ArticleTranslation).where(
        ArticleTranslation.article_id.in_(article_ids), ArticleTranslation.language == language
    )
    result = await db.execute(stmt)
    return {t.article_id: t for t in result.scalars().all()}


async def get_articles_missing_translation(db: AsyncSession, language: str, limit: int = 20) -> list[NewsArticle]:
    """PUBLISHED articles that don't have a `language` translation row
    yet, oldest-missing-first — the same "backlog drains gradually"
    pattern as get_unprocessed_articles (news_repository.py, Q4)."""
    translated_subquery = select(ArticleTranslation.article_id).where(ArticleTranslation.language == language)
    stmt = (
        select(NewsArticle)
        .where(NewsArticle.editorial_status == "PUBLISHED", NewsArticle.id.not_in(translated_subquery))
        .order_by(NewsArticle.published_at.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
