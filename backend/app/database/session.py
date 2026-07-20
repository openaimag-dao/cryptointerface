from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.database.base import Base

settings = get_settings()

engine = create_async_engine(settings.database_url, pool_pre_ping=True, future=True)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a request-scoped async DB session."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_models() -> None:
    """Create tables that don't exist yet.

    Sprint 2 uses `create_all` for simplicity. If the schema needs
    versioned migrations later, introduce Alembic against this same
    metadata (`Base.metadata`) without changing model definitions.
    """
    async with engine.begin() as conn:
        # Import models so they're registered on Base.metadata before create_all.
        from app import models  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)


async def dispose_engine() -> None:
    await engine.dispose()
