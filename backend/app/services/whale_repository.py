"""Persistence for whale events (`app/intelligence/whales/`)."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_engine.types import WhaleSnapshot
from app.models.whale import WhaleEvent

# Which watchlist symbol each on-chain asset corresponds to — only
# symbols with an Ethereum-native presence are covered (see
# app/intelligence/whales/addresses.py's docstring for why).
SYMBOL_TO_ASSET: dict[str, str] = {"ETHUSDT": "ETH", "LINKUSDT": "LINK"}

SNAPSHOT_LOOKBACK_HOURS = 24


async def insert_whale_event(
    db: AsyncSession,
    *,
    asset: str,
    amount: float,
    usd_value: float,
    wallet_type: str,
    direction: str,
    exchange: str | None,
    confidence: float,
    from_address: str,
    to_address: str,
    tx_hash: str,
    timestamp: int,
) -> bool:
    """Returns True if this was a genuinely new event (not a dupe)."""
    stmt = (
        pg_insert(WhaleEvent)
        .values(
            asset=asset,
            amount=amount,
            usd_value=usd_value,
            wallet_type=wallet_type,
            direction=direction,
            exchange=exchange,
            confidence=confidence,
            from_address=from_address,
            to_address=to_address,
            tx_hash=tx_hash,
            timestamp=timestamp,
        )
        .on_conflict_do_nothing(index_elements=["tx_hash"])
        .returning(WhaleEvent.id)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.first() is not None


async def get_recent_whale_events(db: AsyncSession, limit: int = 30, asset: str | None = None) -> list[WhaleEvent]:
    stmt = select(WhaleEvent)
    if asset is not None:
        stmt = stmt.where(WhaleEvent.asset == asset)
    stmt = stmt.order_by(WhaleEvent.timestamp.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_whale_snapshot_for_symbol(db: AsyncSession, symbol: str) -> WhaleSnapshot | None:
    asset = SYMBOL_TO_ASSET.get(symbol)
    if asset is None:
        return None

    cutoff = int(datetime.now(UTC).timestamp()) - SNAPSHOT_LOOKBACK_HOURS * 3600
    stmt = select(WhaleEvent).where(WhaleEvent.asset == asset, WhaleEvent.timestamp >= cutoff)
    result = await db.execute(stmt)
    events = result.scalars().all()
    if not events:
        return None

    to_exchange_usd = sum(e.usd_value for e in events if e.direction == "TO_EXCHANGE")
    from_exchange_usd = sum(e.usd_value for e in events if e.direction == "FROM_EXCHANGE")

    return WhaleSnapshot(
        event_count=len(events),
        to_exchange_usd=to_exchange_usd,
        from_exchange_usd=from_exchange_usd,
    )
