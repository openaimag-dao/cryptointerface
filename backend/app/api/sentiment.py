"""Sentiment Engine API — see app/intelligence/sentiment/engine.py."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.session import get_db
from app.intelligence.sentiment.engine import compute_sentiment
from app.schemas.sentiment import SentimentCategory, SentimentSnapshot
from app.services.sentiment_repository import insert_sentiment_score
from app.utils.timeframes import TIMEFRAME_SECONDS

router = APIRouter(prefix="/api/sentiment", tags=["sentiment"])
settings = get_settings()


@router.get("", response_model=SentimentSnapshot)
async def get_sentiment(
    symbol: str = Query(default=None, description="Defaults to the first configured watchlist symbol"),
    interval: str = Query("1h", description="One of: " + ", ".join(TIMEFRAME_SECONDS)),
    db: AsyncSession = Depends(get_db),
) -> SentimentSnapshot:
    if interval not in TIMEFRAME_SECONDS:
        raise HTTPException(status_code=400, detail=f"Unsupported interval: {interval}")
    symbol = (symbol or settings.symbol_list[0]).upper()

    result = await compute_sentiment(db, symbol, interval)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No candle history yet for {symbol} {interval}")
    await insert_sentiment_score(db, result)

    return SentimentSnapshot(
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
    )
