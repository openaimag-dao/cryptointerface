"""Persistence for Sentiment Engine runs (`app/intelligence/sentiment/`)."""

from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.sentiment.engine import SentimentResult
from app.models.sentiment import SentimentScore


async def insert_sentiment_score(db: AsyncSession, result: SentimentResult) -> None:
    db.add(
        SentimentScore(
            symbol=result.symbol,
            interval=result.interval,
            time=result.timestamp,
            overall_score=result.overall_score,
            confidence=result.confidence,
            direction=result.direction,
            breakdown={name: asdict(factor) for name, factor in result.breakdown.items()},
            reasons=result.reasons,
        )
    )
    await db.commit()


async def get_latest_sentiment_score(db: AsyncSession, symbol: str, interval: str) -> SentimentScore | None:
    stmt = (
        select(SentimentScore)
        .where(SentimentScore.symbol == symbol, SentimentScore.interval == interval)
        .order_by(SentimentScore.time.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalars().first()
