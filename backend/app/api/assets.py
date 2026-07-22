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
    AssetAnalysisOut,
    AssetDerivativesOut,
    AssetHistoryOut,
    AssetOverviewOut,
    AssetSentimentOut,
    AssetSummaryOut,
    AssetTechnicalOut,
    AssetTimelineOut,
    AssetWhalesOut,
    CorrelationReadingOut,
    ExchangeBreakdownOut,
    FundingHistoryPointOut,
    HistoryPointOut,
    IndicatorReadingOut,
    LiquidationClusterOut,
    MacroInfluenceReadingOut,
    RiskAnalysisOut,
    ScenarioOut,
    SentimentRadarOut,
    SignalOutcomeOut,
    SmartMoneyConceptOut,
    TimelineEntryOut,
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
        volume_trend=_indicator_out(overview.volume_trend),
        liquidity_score=_indicator_out(overview.liquidity_score),
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
        exchange_breakdown=[
            ExchangeBreakdownOut(
                exchange=e.exchange,
                status=e.status,
                open_interest=e.open_interest,
                funding_rate=e.funding_rate,
                note=e.note,
            )
            for e in derivatives.exchange_breakdown
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


@router.get("/{symbol}/analysis", response_model=AssetAnalysisOut)
async def get_asset_analysis(
    symbol: str,
    interval: str = Query("1h", description="One of: " + ", ".join(TIMEFRAME_SECONDS)),
    db: AsyncSession = Depends(get_db),
) -> AssetAnalysisOut:
    _validate_interval(interval)
    base_asset = _base_asset(symbol)
    analysis = await asset_service.get_analysis_snapshot(db, base_asset, interval)
    if analysis is None:
        raise HTTPException(status_code=404, detail=f"No candle history yet for {base_asset} {interval}")

    return AssetAnalysisOut(
        symbol=analysis.symbol,
        interval=analysis.interval,
        direction=analysis.direction,
        confidence=round(analysis.confidence, 1),
        market_score=round(analysis.market_score, 1),
        entry=analysis.entry,
        stop=analysis.stop,
        tp1=analysis.tp1,
        tp2=analysis.tp2,
        tp3=analysis.tp3,
        risk_reward=round(analysis.risk_reward, 2) if analysis.risk_reward is not None else None,
        reasons=analysis.reasons,
        scenarios=[
            ScenarioOut(label=s.label, probability=s.probability, conditions=s.conditions, targets=s.targets)
            for s in analysis.scenarios
        ],
        risk=RiskAnalysisOut(
            nearest_support=analysis.risk.nearest_support,
            nearest_resistance=analysis.risk.nearest_resistance,
            atr=analysis.risk.atr,
            atr_risk_pct=analysis.risk.atr_risk_pct,
            volatility_score=analysis.risk.volatility_score,
            risk_level=analysis.risk.risk_level,
            max_recommended_leverage=analysis.risk.max_recommended_leverage,
            drawdown_risk_pct=analysis.risk.drawdown_risk_pct,
        ),
    )


@router.get("/{symbol}/history", response_model=AssetHistoryOut)
async def get_asset_history(
    symbol: str,
    interval: str = Query("1h", description="One of: " + ", ".join(TIMEFRAME_SECONDS)),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> AssetHistoryOut:
    _validate_interval(interval)
    base_asset = _base_asset(symbol)
    history = await asset_service.get_history_snapshot(db, base_asset, interval, limit=limit)
    trading_pair = asset_service.to_trading_pair(base_asset)

    return AssetHistoryOut(
        symbol=trading_pair,
        interval=interval,
        signals=[
            SignalOutcomeOut(
                time=s.analysis.time,
                direction=s.analysis.direction,
                score=round(s.analysis.score, 1),
                confidence=round(s.analysis.confidence, 1),
                entry=s.analysis.entry,
                stop=s.analysis.stop,
                tp1=s.analysis.tp1,
                outcome=s.outcome,
                pnl_percent=round(s.pnl_percent, 2) if s.pnl_percent is not None else None,
            )
            for s in history.signals
        ],
        win_rate=history.win_rate,
        avg_win_pnl_percent=history.avg_win_pnl_percent,
        avg_loss_pnl_percent=history.avg_loss_pnl_percent,
        score_history=[HistoryPointOut(time=t, value=round(v, 1)) for t, v in history.score_history],
        confidence_history=[HistoryPointOut(time=t, value=round(v, 1)) for t, v in history.confidence_history],
    )


@router.get("/{symbol}/correlation", response_model=list[CorrelationReadingOut])
async def get_asset_correlation(
    symbol: str,
    interval: str = Query("1h", description="One of: " + ", ".join(TIMEFRAME_SECONDS)),
    db: AsyncSession = Depends(get_db),
) -> list[CorrelationReadingOut]:
    _validate_interval(interval)
    base_asset = _base_asset(symbol)
    readings = await asset_service.get_correlation_snapshot(db, base_asset, interval)
    return [
        CorrelationReadingOut(reference=r.reference, coefficient=r.coefficient, data_points=r.data_points)
        for r in readings
    ]


@router.get("/{symbol}/timeline", response_model=AssetTimelineOut)
async def get_asset_timeline(
    symbol: str,
    interval: str = Query("1h", description="One of: " + ", ".join(TIMEFRAME_SECONDS)),
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> AssetTimelineOut:
    _validate_interval(interval)
    base_asset = _base_asset(symbol)
    timeline = await asset_service.get_timeline_snapshot(db, base_asset, interval, limit=limit)
    trading_pair = asset_service.to_trading_pair(base_asset)

    return AssetTimelineOut(
        symbol=trading_pair,
        interval=interval,
        entries=[
            TimelineEntryOut(
                time=e.time,
                score=round(e.score, 1),
                confidence=round(e.confidence, 1),
                direction=e.direction,
                change_summary=e.change_summary,
                reasons=e.reasons,
                strengthened_factors=e.strengthened_factors,
                weakened_factors=e.weakened_factors,
                data_status=e.data_status,
            )
            for e in timeline.entries
        ],
    )
