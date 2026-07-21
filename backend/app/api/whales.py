"""Whale Engine API — real (see app/intelligence/whales/): Etherscan-tracked
transfers touching known exchange wallets, classified deterministically.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.whale import WhaleEvent
from app.schemas.whale import WhaleTransaction
from app.services.whale_repository import get_recent_whale_events

router = APIRouter(prefix="/api/whales", tags=["whales"])


def _to_whale_transaction(event: WhaleEvent) -> WhaleTransaction:
    return WhaleTransaction(
        id=str(event.id),
        asset=event.asset,
        amount=event.amount,
        usd_value=round(event.usd_value, 2),
        wallet_type=event.wallet_type,
        direction=event.direction,
        exchange=event.exchange,
        confidence=round(event.confidence, 1),
        from_address=event.from_address,
        to_address=event.to_address,
        tx_hash=event.tx_hash,
        timestamp=datetime.fromtimestamp(event.timestamp, tz=UTC).isoformat(),
    )


@router.get("/transactions", response_model=list[WhaleTransaction])
async def list_whale_transactions(
    count: int = Query(24, ge=1, le=200),
    asset: str | None = Query(default=None, description="e.g. ETH, LINK"),
    db: AsyncSession = Depends(get_db),
) -> list[WhaleTransaction]:
    asset = asset.upper() if asset else None
    events = await get_recent_whale_events(db, limit=count, asset=asset)
    return [_to_whale_transaction(e) for e in events]
