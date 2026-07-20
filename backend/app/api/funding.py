from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.redis import FUNDING_KEY, cache_get_json
from app.database.session import get_db
from app.schemas.funding import FundingRate
from app.services.market_repository import get_latest_funding

router = APIRouter(prefix="/api/funding", tags=["funding"])
settings = get_settings()


async def _build_funding(symbol: str, db: AsyncSession) -> FundingRate | None:
    cached = await cache_get_json(FUNDING_KEY.format(symbol=symbol))
    if cached is not None:
        return FundingRate(
            symbol=symbol,
            funding_rate=cached["funding_rate"],
            mark_price=cached["mark_price"],
            funding_time=cached["funding_time"],
            next_funding_time=cached.get("next_funding_time"),
        )

    row = await get_latest_funding(db, symbol)
    if row is None:
        return None
    return FundingRate(
        symbol=symbol, funding_rate=row.funding_rate, mark_price=row.mark_price, funding_time=row.funding_time
    )


@router.get("", response_model=list[FundingRate])
async def list_funding(db: AsyncSession = Depends(get_db)) -> list[FundingRate]:
    results = []
    for symbol in settings.symbol_list:
        funding = await _build_funding(symbol, db)
        if funding is not None:
            results.append(funding)
    return results


@router.get("/{symbol}", response_model=FundingRate)
async def get_funding(symbol: str, db: AsyncSession = Depends(get_db)) -> FundingRate:
    funding = await _build_funding(symbol.upper(), db)
    if funding is None:
        raise HTTPException(status_code=404, detail=f"No funding data yet for {symbol}")
    return funding
