from fastapi import APIRouter, HTTPException

from app import mock_data
from app.models.market import AssetQuote, Candle, MarketOverview

router = APIRouter(prefix="/api/markets", tags=["markets"])


@router.get("/assets", response_model=list[AssetQuote])
def list_assets() -> list[AssetQuote]:
    return mock_data.get_assets()


@router.get("/assets/{symbol}", response_model=AssetQuote)
def get_asset(symbol: str) -> AssetQuote:
    asset = mock_data.get_asset(symbol.upper())
    if asset is None:
        raise HTTPException(status_code=404, detail=f"Unknown symbol: {symbol}")
    return asset


@router.get("/overview", response_model=MarketOverview)
def get_overview() -> MarketOverview:
    return mock_data.get_market_overview()


@router.get("/candles/{symbol}", response_model=list[Candle])
def get_candles(symbol: str, count: int = 180) -> list[Candle]:
    asset = mock_data.get_asset(symbol.upper())
    base_price = asset.price if asset else 100.0
    return mock_data.get_candles(symbol.upper(), base_price, count)
