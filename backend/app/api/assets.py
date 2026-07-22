"""Asset Intelligence Dashboard API (Sprint 8 spec) — one per-symbol
research terminal, `/assets/{symbol}` on the frontend. Every endpoint is
a thin conversion layer over `app/services/asset_service.py`, which in
turn wraps the existing Data/AI/Intelligence Engines — no new
computation happens in this file.

`symbol` accepts either the bare asset (`BTC`) or the trading pair
(`BTCUSDT`); both normalize to the same base asset before hitting the
service layer.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.news import _to_news_item
from app.api.whales import _to_whale_transaction
from app.database.session import get_db
from app.schemas.asset import (
    AssetDerivativesOut,
    AssetOverviewOut,
    AssetSentimentOut,
    AssetSummaryOut,
    AssetTechnicalOut,
    AssetWhalesOut,
    FundingHistoryPointOut,
    IndicatorReadingOut,
    LiquidationClusterOut,
    MacroInfluenceReadingOut,
    SentimentRadarOut,
    SmartMoneyConceptOut,
)
from app.schemas.news import NewsItem
from app.schemas.sentiment import SentimentCategory
from app.services import asset_service
from app.utils.timeframes import TIMEFRAME_SECONDS

router = APIRouter(prefix="/api/assets", tags=["assets"])


def _base_asset(symbol: str) -> str:
    return asset_service.to_base_asset(symbol)


def _validate_interval(interval: str) -> None:
    if interval not in TIMEFRAME_SECONDS:
        raise HTTPException(status_code=400, detail=f"Unsupported interval: {interval}")


def _indicator_out(reading: asset_service.IndicatorReading) -> IndicatorReadingOut:
    return IndicatorReadingOut(
        name=reading.name, value=reading.value, status=reading.status, explanation=reading.explanation
    )


@router.get("/{symbol}", response_model=AssetSummaryOut)
async def get_asset_summary(
    symbol: str,
    interval: str = Query("1h", description="One of: " + ", ".join(TIMEFRAME_SECONDS)),
    db: AsyncSession = Depends(get_db),
) -> AssetSummaryOut:
    _validate_interval(interval)
    base_asset = _base_asset(symbol)
    summary = await asset_service.get_asset_summary(db, base_asset, interval)
    if summary is None:
        raise HTTPException(status_code=404, detail=f"No market data yet for {base_asset}")

    return AssetSummaryOut(
        symbol=summary.symbol,
        base_asset=summary.base_asset,
        price=summary.price,
        change_percent_24h=summary.change_percent_24h,
        change_percent_7d=summary.change_percent_7d,
        change_percent_30d=summary.change_percent_30d,
        market_cap=summary.market_cap,
        volume_24h=summary.volume_24h,
        funding_rate=summary.funding_rate,
        open_interest=summary.open_interest,
        market_score=summary.market_score,
        confidence=summary.confidence,
        direction=summary.direction,
    )


@router.get("/{symbol}/overview", response_model=AssetOverviewOut)
async def get_asset_overview(
    symbol: str,
    interval: str = Query("1h", description="One of: " + ", ".join(TIMEFRAME_SECONDS)),
    db: AsyncSession = Depends(get_db),
) -> AssetOverviewOut:
    _validate_interval(interval)
    base_asset = _base_asset(symbol)
    overview = await asset_service.get_overview_snapshot(db, base_asset, interval)
    if overview is None:
        raise HTTPException(status_code=404, detail=f"No candle history yet for {base_asset} {interval}")

    return AssetOverviewOut(
        trend_status=overview.trend_status,
        volatility_status=overview.volatility_status,
        atr=_indicator_out(overview.atr),
        rsi=_indicator_out(overview.rsi),
        macd=_indicator_out(overview.macd),
        ema_alignment=_indicator_out(overview.ema_alignment),
        vwap=_indicator_out(overview.vwap),
    )


@router.get("/{symbol}/technical", response_model=AssetTechnicalOut)
async def get_asset_technical(
    symbol: str,
    interval: str = Query("1h", description="One of: " + ", ".join(TIMEFRAME_SECONDS)),
    db: AsyncSession = Depends(get_db),
) -> AssetTechnicalOut:
    _validate_interval(interval)
    base_asset = _base_asset(symbol)
    technical = await asset_service.get_technical_snapshot(db, base_asset, interval)
    if technical is None:
        raise HTTPException(status_code=404, detail=f"No candle history yet for {base_asset} {interval}")

    return AssetTechnicalOut(
        symbol=technical.symbol,
        interval=technical.interval,
        indicators=[_indicator_out(r) for r in technical.indicators],
        smart_money=[
            SmartMoneyConceptOut(name=c.name, status=c.status, value=c.value, explanation=c.explanation)
            for c in technical.smart_money
        ],
        nearest_support=technical.nearest_support,
        nearest_resistance=technical.nearest_resistance,
        breakout_status=technical.breakout_status,
    )


@router.get("/{symbol}/derivatives", response_model=AssetDerivativesOut)
async def get_asset_derivatives(symbol: str, db: AsyncSession = Depends(get_db)) -> AssetDerivativesOut:
    base_asset = _base_asset(symbol)
    derivatives = await asset_service.get_derivatives_snapshot(db, base_asset)

    return AssetDerivativesOut(
        symbol=derivatives.symbol,
        funding_rate=derivatives.funding_rate,
        funding_history=[FundingHistoryPointOut(time=t, rate=r) for t, r in derivatives.funding_history],
        funding_trend=derivatives.funding_trend,
        open_interest=derivatives.open_interest,
        open_interest_value=derivatives.open_interest_value,
        oi_delta_percent=derivatives.oi_delta_percent,
        liquidation_clusters=[
            LiquidationClusterOut(
                price_low=c.price_low, price_high=c.price_high, total_usd=c.total_usd, event_count=c.event_count
            )
            for c in derivatives.liquidation_clusters
        ],
    )


@router.get("/{symbol}/whales", response_model=AssetWhalesOut)
async def get_asset_whales(
    symbol: str, limit: int = Query(30, ge=1, le=200), db: AsyncSession = Depends(get_db)
) -> AssetWhalesOut:
    base_asset = _base_asset(symbol)
    whales = await asset_service.get_whales_snapshot(db, base_asset, limit=limit)

    return AssetWhalesOut(
        symbol=whales.symbol,
        asset=whales.asset,
        whale_score=whales.whale_score,
        events=[_to_whale_transaction(e) for e in whales.events],
        to_exchange_usd_24h=whales.to_exchange_usd_24h,
        from_exchange_usd_24h=whales.from_exchange_usd_24h,
    )


@router.get("/{symbol}/news", response_model=list[NewsItem])
async def get_asset_news(
    symbol: str, limit: int = Query(30, ge=1, le=200), db: AsyncSession = Depends(get_db)
) -> list[NewsItem]:
    base_asset = _base_asset(symbol)
    articles = await asset_service.get_news_snapshot(db, base_asset, limit=limit)
    return [_to_news_item(a) for a in articles]


@router.get("/{symbol}/macro", response_model=list[MacroInfluenceReadingOut])
async def get_asset_macro(symbol: str, db: AsyncSession = Depends(get_db)) -> list[MacroInfluenceReadingOut]:
    _base_asset(symbol)  # validates format; macro backdrop is market-wide, not per-symbol
    readings = await asset_service.get_macro_snapshot(db)
    return [
        MacroInfluenceReadingOut(
            id=r.id,
            label=r.label,
            current=r.current,
            change_percent=r.change_percent,
            trend=r.trend,
            influence=r.influence,
        )
        for r in readings
    ]


@router.get("/{symbol}/sentiment", response_model=AssetSentimentOut)
async def get_asset_sentiment(
    symbol: str,
    interval: str = Query("1h", description="One of: " + ", ".join(TIMEFRAME_SECONDS)),
    db: AsyncSession = Depends(get_db),
) -> AssetSentimentOut:
    _validate_interval(interval)
    base_asset = _base_asset(symbol)
    sentiment = await asset_service.get_sentiment_snapshot(db, base_asset, interval)
    if sentiment is None:
        raise HTTPException(status_code=404, detail=f"No candle history yet for {base_asset} {interval}")

    result = sentiment.result
    return AssetSentimentOut(
        symbol=result.symbol,
        interval=result.interval,
        timestamp=result.timestamp,
        overall_score=round(result.overall_score, 1),
        confidence=round(result.confidence, 1),
        direction=result.direction,
        breakdown={
            name: SentimentCategory(
                score=round(factor.score, 1),
                direction=factor.direction,
                confidence=round(factor.confidence, 1),
                reasons=factor.reasons,
            )
            for name, factor in result.breakdown.items()
        },
        reasons=result.reasons,
        radar=SentimentRadarOut(
            news=round(sentiment.radar.news, 1),
            social=sentiment.radar.social,
            whale=round(sentiment.radar.whale, 1),
            technical=round(sentiment.radar.technical, 1),
            macro=round(sentiment.radar.macro, 1),
            market_score=round(sentiment.radar.market_score, 1),
        ),
    )
