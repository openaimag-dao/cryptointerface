"""Real liquidation data, fed by Binance's `forceOrder` WebSocket stream
(see `app/tasks/live_feed.py`'s `_handle_liquidation`) and persisted to
the `liquidations` table.

The heatmap buckets recent liquidations by price into `count` bins around
the current price range — it reflects genuinely observed liquidations, so
it may look sparse until enough events have accumulated (this stream only
started recording once the Data Engine started; there's no historical
liquidation backfill).
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.liquidation import LiquidationEvent, LiquidationHeatmapCell, LiquidationTotals
from app.services.market_repository import get_liquidation_totals_24h, get_recent_liquidations

router = APIRouter(prefix="/api/liquidations", tags=["liquidations"])


def _to_liquidation_out(row) -> LiquidationEvent:
    return LiquidationEvent(
        id=str(row.id),
        symbol=row.symbol,
        side=row.side,
        amount_usd=row.amount_usd,
        price=row.price,
        exchange=row.exchange,
        timestamp=datetime.fromtimestamp(row.timestamp / 1000, tz=UTC).isoformat(),
    )


@router.get("", response_model=list[LiquidationEvent])
async def list_liquidations(
    count: int = Query(30, ge=1, le=200), db: AsyncSession = Depends(get_db)
) -> list[LiquidationEvent]:
    rows = await get_recent_liquidations(db, limit=count)
    return [_to_liquidation_out(row) for row in rows]


@router.get("/totals", response_model=LiquidationTotals)
async def get_totals(db: AsyncSession = Depends(get_db)) -> LiquidationTotals:
    totals = await get_liquidation_totals_24h(db)
    return LiquidationTotals(long_usd=totals["LONG"], short_usd=totals["SHORT"])


@router.get("/heatmap", response_model=list[LiquidationHeatmapCell])
async def get_heatmap(
    symbol: str = "BTCUSDT", count: int = Query(40, ge=1, le=200), db: AsyncSession = Depends(get_db)
) -> list[LiquidationHeatmapCell]:
    rows = await get_recent_liquidations(db, limit=500, symbol=symbol.upper())
    if not rows:
        return []

    prices = [row.price for row in rows]
    low, high = min(prices), max(prices)
    if low == high:
        return [LiquidationHeatmapCell(price=low, intensity=1.0)]

    bucket_width = (high - low) / count
    buckets = [0.0] * count
    for row in rows:
        index = min(count - 1, int((row.price - low) / bucket_width))
        buckets[index] += row.amount_usd

    max_bucket = max(buckets) or 1.0
    return [
        LiquidationHeatmapCell(price=round(low + bucket_width * (i + 0.5), 2), intensity=round(value / max_bucket, 4))
        for i, value in enumerate(buckets)
        if value > 0
    ]
