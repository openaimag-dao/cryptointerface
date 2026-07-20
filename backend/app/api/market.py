from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.redis import FUNDING_KEY, OPEN_INTEREST_KEY, TICKER_KEY, cache_get_json
from app.database.session import get_db
from app.schemas.market import MarketAsset
from app.services.market_repository import get_market_stat

router = APIRouter(prefix="/api/market", tags=["market"])
settings = get_settings()


async def _build_market_asset(symbol: str, db: AsyncSession) -> MarketAsset | None:
    ticker = await cache_get_json(TICKER_KEY.format(symbol=symbol))
    if ticker is not None:
        updated_at = datetime.now(UTC).isoformat()
    else:
        stat = await get_market_stat(db, symbol)
        if stat is None:
            return None
        ticker = {
            "price": stat.price,
            "change_percent_24h": stat.change_percent_24h,
            "high_24h": stat.high_24h,
            "low_24h": stat.low_24h,
            "volume_24h": stat.volume_24h,
            "quote_volume_24h": stat.quote_volume_24h,
        }
        updated_at = stat.updated_at.isoformat()

    funding = await cache_get_json(FUNDING_KEY.format(symbol=symbol))
    open_interest = await cache_get_json(OPEN_INTEREST_KEY.format(symbol=symbol))

    return MarketAsset(
        symbol=symbol,
        price=ticker["price"],
        change_percent_24h=ticker["change_percent_24h"],
        high_24h=ticker["high_24h"],
        low_24h=ticker["low_24h"],
        volume_24h=ticker["volume_24h"],
        quote_volume_24h=ticker["quote_volume_24h"],
        funding_rate=funding["funding_rate"] if funding else None,
        open_interest=open_interest["open_interest"] if open_interest else None,
        updated_at=updated_at,
    )


@router.get("", response_model=list[MarketAsset])
async def list_market_assets(db: AsyncSession = Depends(get_db)) -> list[MarketAsset]:
    assets = []
    for symbol in settings.symbol_list:
        asset = await _build_market_asset(symbol, db)
        if asset is not None:
            assets.append(asset)
    return assets


@router.get("/{symbol}", response_model=MarketAsset)
async def get_market_asset(symbol: str, db: AsyncSession = Depends(get_db)) -> MarketAsset:
    asset = await _build_market_asset(symbol.upper(), db)
    if asset is None:
        raise HTTPException(status_code=404, detail=f"No market data yet for {symbol}")
    return asset
