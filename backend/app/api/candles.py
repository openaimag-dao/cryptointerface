from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.candle import Candle
from app.services.market_repository import get_recent_candles, to_candle_schema
from app.utils.timeframes import TIMEFRAME_SECONDS

router = APIRouter(prefix="/api/candles", tags=["candles"])


@router.get("/{symbol}", response_model=list[Candle])
async def get_candles(
    symbol: str,
    interval: str = Query("1h", description="One of: " + ", ".join(TIMEFRAME_SECONDS)),
    limit: int = Query(500, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
) -> list[Candle]:
    if interval not in TIMEFRAME_SECONDS:
        raise HTTPException(status_code=400, detail=f"Unsupported interval: {interval}")

    candles = await get_recent_candles(db, symbol.upper(), interval, limit=limit)
    return [to_candle_schema(candle) for candle in candles]
