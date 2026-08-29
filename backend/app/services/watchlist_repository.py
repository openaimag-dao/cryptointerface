from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.watchlist_item import WatchlistItem


async def add_watchlist_symbol(db: AsyncSession, *, user_id: int, symbol: str) -> bool:
    stmt = (
        pg_insert(WatchlistItem)
        .values(user_id=user_id, symbol=symbol)
        .on_conflict_do_nothing(index_elements=["user_id", "symbol"])
        .returning(WatchlistItem.id)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.first() is not None


async def remove_watchlist_symbol(db: AsyncSession, *, user_id: int, symbol: str) -> bool:
    stmt = select(WatchlistItem).where(WatchlistItem.user_id == user_id, WatchlistItem.symbol == symbol)
    result = await db.execute(stmt)
    item = result.scalars().first()
    if item is None:
        return False
    await db.delete(item)
    await db.commit()
    return True


async def list_watchlist_symbols(db: AsyncSession, user_id: int) -> list[str]:
    stmt = (
        select(WatchlistItem.symbol).where(WatchlistItem.user_id == user_id).order_by(WatchlistItem.created_at.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
