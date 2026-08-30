"""Regression test for a real bug caught by manual verification, not the
test suite: `create_all` only creates brand-new tables — it silently does
nothing for a column added to an already-existing one (e.g. `news`, live
since Sprint 4), so every insert/select against that table starts failing
with `UndefinedColumnError` in any environment that already had data
before the column was added. `_apply_lightweight_migrations` is the fix;
this locks in that it actually adds the missing columns, and that it's
safe to call repeatedly (every app startup calls it unconditionally).
"""

import re

import pytest
from sqlalchemy import text

from app.database.base import Base
from app.database.session import _MIGRATION_STATEMENTS, _apply_lightweight_migrations, engine
from app.models.news import NewsArticle

# The columns the `news` table had before any lightweight migration ever
# ran (i.e. what `create_all` alone would produce for a table that's
# existed since before this mechanism was introduced). Every column added
# to NewsArticle since then must have a matching `ALTER TABLE ... ADD
# COLUMN` statement, or production rows created before the column existed
# never get it — see test_migration_columns_match_the_current_news_article_model.
_ORIGINAL_NEWS_COLUMNS = {
    "id",
    "created_at",
    "source",
    "title",
    "summary",
    "url",
    "published_at",
    "language",
    "symbols",
    "impact_score",
    "sentiment",
    "category",
}


@pytest.mark.asyncio
async def test_apply_lightweight_migrations_adds_missing_columns_to_an_existing_table():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            # Simulate a pre-Q1 deployment: the `news` table exists, but
            # without the columns this migration is responsible for adding.
            await conn.execute(text("ALTER TABLE news DROP COLUMN slug"))
            await conn.execute(text("ALTER TABLE news DROP COLUMN editorial_status"))

            await _apply_lightweight_migrations(conn)

            result = await conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'news' AND column_name IN ('slug', 'editorial_status')"
                )
            )
            columns = {row[0] for row in result}
            assert columns == {"slug", "editorial_status"}

            await conn.execute(
                text(
                    "INSERT INTO news (source, title, summary, url, published_at, language, symbols, "
                    "impact_score, sentiment, category, created_at) VALUES "
                    "('S', 'T', 'Sum', 'https://example.com/migration-test', 0, 'en', '[]', 0, 'NEUTRAL', "
                    "'Market', now())"
                )
            )
    finally:
        # Same event-loop-per-test constraint as conftest.py's db_session
        # fixture: dispose forces fresh connections on the next test's loop.
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()


@pytest.mark.asyncio
async def test_apply_lightweight_migrations_is_idempotent():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

            await _apply_lightweight_migrations(conn)
            await _apply_lightweight_migrations(conn)  # must not raise on the second call
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest.mark.asyncio
async def test_one_failing_statement_does_not_roll_back_the_others():
    """Regression test for a real production incident: every `NewsArticle`
    query 500ing (even a lookup for a nonexistent id — the SELECT itself
    failed) while unrelated tables kept working, because all these
    statements ran in one shared transaction and one failing statement
    (plausibly `CREATE UNIQUE INDEX uq_news_slug` against data with a
    real duplicate slug — reproduced here) silently rolled back every
    `ADD COLUMN` that had already "succeeded" earlier in the same call,
    while the app still came up with no visible startup error. Each
    statement now runs in its own SAVEPOINT, so one failure must not
    block the ones before or after it in the list."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(text("ALTER TABLE news DROP COLUMN image_url"))
            # The model's own __table_args__ already declares this
            # constraint, so create_all just added it — drop it back off to
            # simulate a real pre-existing table from before `slug` had a
            # uniqueness guarantee, which is exactly the scenario
            # _apply_lightweight_migrations's own CREATE UNIQUE INDEX
            # statement exists to backfill.
            await conn.execute(text("ALTER TABLE news DROP CONSTRAINT uq_news_slug"))

            # Two rows with the same non-null slug — CREATE UNIQUE INDEX
            # uq_news_slug (a statement in the *middle* of the list) is
            # guaranteed to fail against this real duplicate-key violation.
            await conn.execute(
                text(
                    "INSERT INTO news (source, title, summary, url, published_at, language, symbols, "
                    "impact_score, sentiment, category, editorial_status, slug, created_at) VALUES "
                    "('S', 'T1', 'Sum', 'https://example.com/dup-slug-1', 0, 'en', '[]', 0, 'NEUTRAL', "
                    "'Market', 'PUBLISHED', 'duplicate-slug', now()), "
                    "('S', 'T2', 'Sum', 'https://example.com/dup-slug-2', 0, 'en', '[]', 0, 'NEUTRAL', "
                    "'Market', 'PUBLISHED', 'duplicate-slug', now())"
                )
            )

            await _apply_lightweight_migrations(conn)  # must not raise

            columns = await conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'news' AND column_name = 'image_url'"
                )
            )
            assert columns.first() is not None, "a column earlier in the list must still be added"

            indexes = await conn.execute(
                text("SELECT indexname FROM pg_indexes WHERE tablename = 'news' AND indexname = :name"),
                {"name": "ix_news_search_vector"},
            )
            assert indexes.first() is not None, "a statement later in the list must still run"
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


def test_migration_columns_match_the_current_news_article_model():
    """Regression test for a real production incident: `portal_topic` was
    added to NewsArticle with no matching `ALTER TABLE ... ADD COLUMN`
    statement in `_apply_lightweight_migrations`, so it never reached the
    live `news` table and every query against it 500'd (see that
    function's docstring). This diffs the model's columns against the
    columns the migration statements actually add, so any future column
    added to NewsArticle without a matching statement fails the build
    instead of production."""
    model_columns = {c.name for c in NewsArticle.__table__.columns}
    added_columns = {
        match.group(1)
        for statement in _MIGRATION_STATEMENTS
        if (match := re.search(r"ADD COLUMN IF NOT EXISTS (\w+)", statement))
    }
    assert model_columns - _ORIGINAL_NEWS_COLUMNS == added_columns
