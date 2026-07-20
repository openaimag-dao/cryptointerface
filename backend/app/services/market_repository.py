"""Async persistence helpers shared by the historical loader and live feed.

Every write is an idempotent upsert (`INSERT ... ON CONFLICT DO UPDATE`) so
replaying the same candle/funding/OI update — which happens naturally with
overlapping REST backfills and WS re-deliveries after a reconnect — never
creates duplicate rows.
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candle import Candle
from app.models.funding import FundingRate
from app.models.indicator_value import IndicatorValue
from app.models.market_stat import MarketStat
from app.models.open_interest import OpenInterest
from app.models.symbol import Symbol
from app.schemas.candle import Candle as CandleSchema
from app.schemas.indicator import IndicatorSnapshot
from app.services.binance.rest_client import KlineData


def to_candle_schema(candle: Candle) -> CandleSchema:
    """Maps the ORM row (`open_time`) to the API/indicator-engine shape (`time`)."""
    return CandleSchema(
        time=candle.open_time,
        open=candle.open,
        high=candle.high,
        low=candle.low,
        close=candle.close,
        volume=candle.volume,
    )


async def upsert_symbol(db: AsyncSession, symbol: str, base_asset: str, quote_asset: str) -> None:
    stmt = (
        pg_insert(Symbol)
        .values(symbol=symbol, base_asset=base_asset, quote_asset=quote_asset)
        .on_conflict_do_nothing(index_elements=["symbol"])
    )
    await db.execute(stmt)
    await db.commit()


async def upsert_candle(db: AsyncSession, symbol: str, interval: str, kline: KlineData, is_closed: bool = True) -> None:
    stmt = pg_insert(Candle).values(
        symbol=symbol,
        interval=interval,
        open_time=kline.open_time // 1000,
        close_time=kline.close_time // 1000,
        open=kline.open,
        high=kline.high,
        low=kline.low,
        close=kline.close,
        volume=kline.volume,
        quote_volume=kline.quote_volume,
        trades=kline.trades,
        is_closed=is_closed,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["symbol", "interval", "open_time"],
        set_={
            "close_time": stmt.excluded.close_time,
            "open": stmt.excluded.open,
            "high": stmt.excluded.high,
            "low": stmt.excluded.low,
            "close": stmt.excluded.close,
            "volume": stmt.excluded.volume,
            "quote_volume": stmt.excluded.quote_volume,
            "trades": stmt.excluded.trades,
            "is_closed": stmt.excluded.is_closed,
        },
    )
    await db.execute(stmt)
    await db.commit()


# Postgres/asyncpg caps bound parameters at 32767 per statement. Candle rows
# bind 12 columns each, so this stays comfortably under that ceiling.
_CANDLE_BATCH_SIZE = 1000


async def bulk_upsert_candles(db: AsyncSession, symbol: str, interval: str, klines: list[KlineData]) -> None:
    if not klines:
        return

    rows = [
        {
            "symbol": symbol,
            "interval": interval,
            "open_time": k.open_time // 1000,
            "close_time": k.close_time // 1000,
            "open": k.open,
            "high": k.high,
            "low": k.low,
            "close": k.close,
            "volume": k.volume,
            "quote_volume": k.quote_volume,
            "trades": k.trades,
            "is_closed": True,
        }
        for k in klines
    ]

    for i in range(0, len(rows), _CANDLE_BATCH_SIZE):
        batch = rows[i : i + _CANDLE_BATCH_SIZE]
        stmt = pg_insert(Candle).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "interval", "open_time"],
            set_={
                "close_time": stmt.excluded.close_time,
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "volume": stmt.excluded.volume,
                "quote_volume": stmt.excluded.quote_volume,
                "trades": stmt.excluded.trades,
                "is_closed": stmt.excluded.is_closed,
            },
        )
        await db.execute(stmt)
        await db.commit()


async def get_recent_candles(db: AsyncSession, symbol: str, interval: str, limit: int = 500) -> list[Candle]:
    stmt = (
        select(Candle)
        .where(Candle.symbol == symbol, Candle.interval == interval)
        .order_by(Candle.open_time.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    candles = list(result.scalars().all())
    candles.reverse()  # ascending (oldest -> newest)
    return candles


async def count_candles(db: AsyncSession, symbol: str, interval: str) -> int:
    stmt = select(Candle.id).where(Candle.symbol == symbol, Candle.interval == interval)
    result = await db.execute(stmt)
    return len(result.all())


async def upsert_market_stat(
    db: AsyncSession,
    symbol: str,
    price: float,
    change_percent_24h: float,
    high_24h: float,
    low_24h: float,
    volume_24h: float,
    quote_volume_24h: float,
) -> None:
    stmt = pg_insert(MarketStat).values(
        symbol=symbol,
        price=price,
        change_percent_24h=change_percent_24h,
        high_24h=high_24h,
        low_24h=low_24h,
        volume_24h=volume_24h,
        quote_volume_24h=quote_volume_24h,
        updated_at=datetime.now(UTC),
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["symbol"],
        set_={
            "price": stmt.excluded.price,
            "change_percent_24h": stmt.excluded.change_percent_24h,
            "high_24h": stmt.excluded.high_24h,
            "low_24h": stmt.excluded.low_24h,
            "volume_24h": stmt.excluded.volume_24h,
            "quote_volume_24h": stmt.excluded.quote_volume_24h,
            "updated_at": stmt.excluded.updated_at,
        },
    )
    await db.execute(stmt)
    await db.commit()


async def get_all_market_stats(db: AsyncSession) -> list[MarketStat]:
    result = await db.execute(select(MarketStat).order_by(MarketStat.symbol))
    return list(result.scalars().all())


async def get_market_stat(db: AsyncSession, symbol: str) -> MarketStat | None:
    result = await db.execute(select(MarketStat).where(MarketStat.symbol == symbol))
    return result.scalar_one_or_none()


async def insert_funding(
    db: AsyncSession, symbol: str, funding_rate: float, mark_price: float, funding_time: int
) -> None:
    stmt = (
        pg_insert(FundingRate)
        .values(symbol=symbol, funding_rate=funding_rate, mark_price=mark_price, funding_time=funding_time)
        .on_conflict_do_update(
            index_elements=["symbol", "funding_time"],
            set_={"funding_rate": funding_rate, "mark_price": mark_price},
        )
    )
    await db.execute(stmt)
    await db.commit()


async def get_latest_funding(db: AsyncSession, symbol: str) -> FundingRate | None:
    stmt = select(FundingRate).where(FundingRate.symbol == symbol).order_by(FundingRate.funding_time.desc()).limit(1)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_recent_funding_history(db: AsyncSession, symbol: str, limit: int = 20) -> list[FundingRate]:
    """Most recent `limit` funding readings, ascending (oldest -> newest)."""
    stmt = (
        select(FundingRate).where(FundingRate.symbol == symbol).order_by(FundingRate.funding_time.desc()).limit(limit)
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    rows.reverse()
    return rows


async def insert_open_interest(
    db: AsyncSession, symbol: str, open_interest: float, open_interest_value: float, timestamp: int
) -> None:
    stmt = (
        pg_insert(OpenInterest)
        .values(
            symbol=symbol, open_interest=open_interest, open_interest_value=open_interest_value, timestamp=timestamp
        )
        .on_conflict_do_update(
            index_elements=["symbol", "timestamp"],
            set_={"open_interest": open_interest, "open_interest_value": open_interest_value},
        )
    )
    await db.execute(stmt)
    await db.commit()


async def get_latest_open_interest(db: AsyncSession, symbol: str) -> OpenInterest | None:
    stmt = select(OpenInterest).where(OpenInterest.symbol == symbol).order_by(OpenInterest.timestamp.desc()).limit(1)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_recent_open_interest_history(db: AsyncSession, symbol: str, limit: int = 20) -> list[OpenInterest]:
    """Most recent `limit` open-interest polls, ascending (oldest -> newest)."""
    stmt = (
        select(OpenInterest).where(OpenInterest.symbol == symbol).order_by(OpenInterest.timestamp.desc()).limit(limit)
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    rows.reverse()
    return rows


async def upsert_indicator_value(db: AsyncSession, snapshot: IndicatorSnapshot) -> None:
    stmt = pg_insert(IndicatorValue).values(
        symbol=snapshot.symbol,
        interval=snapshot.interval,
        time=snapshot.time,
        payload=snapshot.model_dump(exclude={"symbol", "interval", "time"}),
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["symbol", "interval", "time"],
        set_={"payload": stmt.excluded.payload},
    )
    await db.execute(stmt)
    await db.commit()


async def get_latest_indicator_value(db: AsyncSession, symbol: str, interval: str) -> IndicatorValue | None:
    stmt = (
        select(IndicatorValue)
        .where(IndicatorValue.symbol == symbol, IndicatorValue.interval == interval)
        .order_by(IndicatorValue.time.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
