"""Persistence for macro-indicator readings (`app/intelligence/macro/`).

Append-only, one row per fetch (see `MacroDataPoint`) — a fetch that hits
the exact same value as last time still gets its own row, so the history
line is a faithful record of "value at time of fetch", not a deduplicated
change log. Volume is low (one write per indicator per poll interval, see
`MACRO_POLL_INTERVAL_SECONDS`), so this is cheap.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_engine.types import MacroIndicatorReading, MacroSnapshot
from app.models.macro import MacroDataPoint

# Maps MacroSnapshot's field names to the indicator slugs stored in the DB
# (see app/intelligence/macro/symbols.py for the provider side of this).
_SNAPSHOT_FIELDS = ("dxy", "gold", "sp500", "nasdaq", "vix", "us10y", "fear_greed", "btc_dominance")


async def insert_macro_point(db: AsyncSession, indicator: str, value: float, source: str, fetched_at: int) -> None:
    db.add(MacroDataPoint(indicator=indicator, value=value, source=source, fetched_at=fetched_at))
    await db.commit()


async def get_latest_points(db: AsyncSession, indicator: str, limit: int = 2) -> list[MacroDataPoint]:
    """Most recent `limit` readings for one indicator, newest first."""
    stmt = (
        select(MacroDataPoint)
        .where(MacroDataPoint.indicator == indicator)
        .order_by(MacroDataPoint.fetched_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_history(db: AsyncSession, indicator: str, limit: int = 100) -> list[MacroDataPoint]:
    """Recent history for one indicator, ascending (oldest -> newest) —
    the shape a chart wants."""
    stmt = (
        select(MacroDataPoint)
        .where(MacroDataPoint.indicator == indicator)
        .order_by(MacroDataPoint.fetched_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(reversed(result.scalars().all()))


def _reading_from_points(points: list[MacroDataPoint]) -> MacroIndicatorReading | None:
    if not points:
        return None
    latest = points[0].value
    if len(points) < 2 or points[1].value == 0:
        return MacroIndicatorReading(value=latest, change_percent=None)
    previous = points[1].value
    change_percent = (latest - previous) / abs(previous) * 100
    return MacroIndicatorReading(value=latest, change_percent=change_percent)


async def get_latest_macro_snapshot(db: AsyncSession) -> MacroSnapshot | None:
    """Builds the `ai_engine`-facing snapshot from the latest two readings
    per indicator (for a change-vs-previous %). Returns `None` only if
    *no* indicator has ever been fetched — `score_macro()` treats that as
    "macro not configured yet", same as the Sprint 3 stub behaved."""
    readings: dict[str, MacroIndicatorReading | None] = {}
    for field in _SNAPSHOT_FIELDS:
        points = await get_latest_points(db, field, limit=2)
        readings[field] = _reading_from_points(points)

    if all(reading is None for reading in readings.values()):
        return None
    return MacroSnapshot(**readings)
