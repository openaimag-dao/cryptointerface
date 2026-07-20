from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.indicator import IndicatorSnapshot
from app.services.market_repository import get_latest_indicator_value
from app.utils.timeframes import TIMEFRAME_SECONDS

router = APIRouter(prefix="/api/indicators", tags=["indicators"])


@router.get("/{symbol}", response_model=IndicatorSnapshot)
async def get_indicators(
    symbol: str,
    interval: str = Query("1h", description="One of: " + ", ".join(TIMEFRAME_SECONDS)),
    db: AsyncSession = Depends(get_db),
) -> IndicatorSnapshot:
    if interval not in TIMEFRAME_SECONDS:
        raise HTTPException(status_code=400, detail=f"Unsupported interval: {interval}")

    row = await get_latest_indicator_value(db, symbol.upper(), interval)
    if row is None:
        raise HTTPException(status_code=404, detail=f"No indicator data yet for {symbol} {interval}")

    return IndicatorSnapshot(symbol=row.symbol, interval=row.interval, time=row.time, **row.payload)
