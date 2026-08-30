from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.logging import get_logger
from app.database.base import Base

settings = get_settings()
logger = get_logger(__name__)

engine = create_async_engine(settings.database_url, pool_pre_ping=True, future=True)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a request-scoped async DB session."""
    async with AsyncSessionLocal() as session:
        yield session


_MIGRATION_STATEMENTS = [
    "ALTER TABLE news ADD COLUMN IF NOT EXISTS portal_topic VARCHAR(16)",
    "ALTER TABLE news ADD COLUMN IF NOT EXISTS slug VARCHAR(140)",
    "ALTER TABLE news ADD COLUMN IF NOT EXISTS editorial_status VARCHAR(16) NOT NULL DEFAULT 'PUBLISHED'",
    "ALTER TABLE news ADD COLUMN IF NOT EXISTS news_event_id BIGINT REFERENCES news_events(id)",
    "ALTER TABLE news ADD COLUMN IF NOT EXISTS author_id BIGINT REFERENCES authors(id)",
    "ALTER TABLE news ADD COLUMN IF NOT EXISTS ai_summary VARCHAR(1000)",
    "ALTER TABLE news ADD COLUMN IF NOT EXISTS image_url VARCHAR(1000)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_news_slug ON news (slug)",
    # Q6: real Postgres full-text search (news_repository.py::search_news)
    # over title (weight A) + summary (weight B) — a GIN expression
    # index, not a stored column, so it needs no backfill for rows that
    # already exist. Must match search_news's expression exactly or
    # Postgres won't use it (query stays correct, just unindexed).
    "CREATE INDEX IF NOT EXISTS ix_news_search_vector ON news "
    "USING gin ((setweight(to_tsvector('english', title), 'A') || "
    "setweight(to_tsvector('english', summary), 'B')))",
]


async def _apply_lightweight_migrations(conn: AsyncConnection) -> None:
    """`create_all` only creates brand-new tables — it never ALTERs one
    that already exists in a running deployment, so a column added to an
    existing model (e.g. NewsArticle.slug in Q1, added to a `news` table
    that's been live since Sprint 4) silently never reaches production
    schema and every insert then fails. `IF NOT EXISTS` makes each
    statement idempotent and safe to run on every startup, including
    against a brand-new DB where create_all already added the column
    (this becomes a no-op there).

    If this list keeps growing, that's the signal to introduce Alembic
    against this same metadata (`Base.metadata`) instead of extending it
    further — this is a deliberate stop-gap, not the long-term answer.

    Each statement runs in its own SAVEPOINT (`conn.begin_nested()`) —
    without this, a single bad statement (e.g. an index build that hits a
    lock timeout, or any other transient error) would abort the *shared*
    outer transaction this function runs in, which Postgres then silently
    rolls back in full, including every `ADD COLUMN` that had already
    "succeeded" earlier in this same call. That previously surfaced as a
    genuine production incident: every `NewsArticle` query 500ing (even a
    lookup for a nonexistent id, which never reaches Pydantic/response
    code — the SELECT itself failed) while completely unrelated tables
    kept working fine, because the whole migration batch silently never
    committed and the app came up anyway. A per-statement savepoint means
    one bad statement is logged and skipped, not a silent, total rollback
    of this entire function with no visible startup error.

    A savepoint only protects against a statement that's *present* here
    failing — it does nothing if a column was added to the model and
    simply never got a matching statement in the first place. That's a
    second, distinct incident this same function has caused: `portal_topic`
    (added to NewsArticle in the "News Portal P1" commit) shipped with no
    `ADD COLUMN` statement at all, so every `news` SELECT 500'd in
    production — including a lookup by a nonexistent id — because Postgres
    doesn't have the column the ORM's SELECT lists, and this had nothing to
    do with the transaction-rollback bug above (fixed first, but the
    symptom didn't change, which is what pointed at a second cause).
    `test_migration_columns_match_the_current_news_article_model` in
    tests/test_database_migrations.py is the tripwire for this specific
    failure mode: it fails the build if any future column added to
    NewsArticle doesn't have a matching statement here.
    """
    for statement in _MIGRATION_STATEMENTS:
        try:
            async with conn.begin_nested():
                await conn.execute(text(statement))
        except DBAPIError:
            logger.warning("lightweight_migration_statement_failed", extra={"statement": statement}, exc_info=True)


async def init_models() -> None:
    """Create tables that don't exist yet, then apply any pending
    lightweight migrations for tables that already did (see
    `_apply_lightweight_migrations`).

    Sprint 2 uses `create_all` for simplicity. If the schema needs
    versioned migrations later, introduce Alembic against this same
    metadata (`Base.metadata`) without changing model definitions.
    """
    async with engine.begin() as conn:
        # Import models so they're registered on Base.metadata before create_all.
        from app import models  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)
        await _apply_lightweight_migrations(conn)


async def dispose_engine() -> None:
    await engine.dispose()
