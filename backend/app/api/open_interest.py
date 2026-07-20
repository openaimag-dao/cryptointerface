from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.redis import OPEN_INTEREST_KEY, cache_get_json
from app.database.session import get_db
from app.schemas.open_interest import OpenInterest
from app.services.market_repository import get_latest_open_interest

router = APIRouter(prefix="/api/open-interest", tags=["open-interest"])
settings = get_settings()


async def _build_open_interest(symbol: str, db: AsyncSession) -> OpenInterest | None:
    cached = await cache_get_json(OPEN_INTEREST_KEY.format(symbol=symbol))
    if cached is not None:
        return OpenInterest(**cached)

    row = await get_latest_open_interest(db, symbol)
    if row is None:
        return None
    return OpenInterest(
        symbol=symbol,
        open_interest=row.open_interest,
        open_interest_value=row.open_interest_value,
        timestamp=row.timestamp,
    )


@router.get("", response_model=list[OpenInterest])
async def list_open_interest(db: AsyncSession = Depends(get_db)) -> list[OpenInterest]:
    results = []
    for symbol in settings.symbol_list:
        oi = await _build_open_interest(symbol, db)
        if oi is not None:
            results.append(oi)
    return results


@router.get("/{symbol}", response_model=OpenInterest)
async def get_open_interest(symbol: str, db: AsyncSession = Depends(get_db)) -> OpenInterest:
    oi = await _build_open_interest(symbol.upper(), db)
    if oi is None:
        raise HTTPException(status_code=404, detail=f"No open interest data yet for {symbol}")
    return oi
