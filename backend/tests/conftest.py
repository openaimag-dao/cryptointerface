import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://aimag:aimag@localhost:5432/aimag_test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")

import pytest_asyncio  # noqa: E402

from app.database.base import Base  # noqa: E402
from app.database.session import AsyncSessionLocal  # noqa: E402


@pytest_asyncio.fixture
async def db_session():
    """Fresh schema per test against the local Postgres test database.

    Disposes the engine's connection pool after each test: pytest-asyncio
    gives every test function its own event loop by default, but SQLAlchemy's
    async engine caches asyncpg connections bound to whichever loop created
    them — reusing the pool across tests raises "attached to a different
    loop". Disposing forces fresh connections on the next test's loop.
    """
    import app.models  # noqa: F401
    from app.database.session import engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _reset_redis_pool():
    """Same event-loop-per-test problem as the DB engine above, for the
    module-level Redis client: disconnect its pool after each test so the
    next test's loop opens fresh connections instead of reusing stale ones.
    """
    from app.core.redis import redis_client

    yield
    await redis_client.connection_pool.disconnect()
