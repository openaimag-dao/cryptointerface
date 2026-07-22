"""Macro indicators — real (see app/intelligence/macro/). `/events` (an
economic calendar: FOMC/NFP/CPI dates) is still mock — that needs its own
provider (e.g. a paid economic-calendar API) and is out of scope for this
sprint; nothing in the spec's Macro Engine section asked for it.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import mock_data
from app.database.session import get_db
from app.intelligence.macro.symbols import MACRO_INDICATORS, MacroIndicatorDef
from app.schemas.macro import MacroEvent, MacroIndicator, MacroSentiment
from app.services.macro_repository import get_latest_points

router = APIRouter(prefix="/api/macro", tags=["macro"])

# Which direction of change reads as crypto-bullish for each unit type.
# "inverted" means a rising value is bearish (mirrors score_macro()'s
# read of the same fields, kept in sync manually since one is display
# formatting and the other is scoring math).
_INVERTED_FIELDS = {"dxy", "vix", "us10y", "gold"}
_NOT_SCORED_NEUTRAL_DISPLAY = {"silver", "oil", "btc_dominance"}


def _format_value(indicator: MacroIndicatorDef, value: float) -> str:
    if indicator.id == "fear_greed":
        return f"{value:.0f}"
    if indicator.id in ("us10y", "btc_dominance"):
        return f"{value:.2f}%"
    return f"${value:,.2f}"


def _format_change_label(change_percent: float | None) -> str:
    if change_percent is None:
        return "—"
    return f"{change_percent:+.2f}%"


def _sentiment_for(indicator_id: str, change_percent: float | None) -> MacroSentiment:
    if indicator_id in _NOT_SCORED_NEUTRAL_DISPLAY or change_percent is None:
        return "NEUTRAL"
    if indicator_id == "fear_greed":
        return "NEUTRAL"  # level-based, not change-based — see score_macro()
    if change_percent == 0:
        return "NEUTRAL"
    moved_up = change_percent > 0
    is_bullish = moved_up != (indicator_id in _INVERTED_FIELDS)
    return "POSITIVE" if is_bullish else "NEGATIVE"


@router.get("/indicators", response_model=list[MacroIndicator])
async def list_indicators(db: AsyncSession = Depends(get_db)) -> list[MacroIndicator]:
    indicators: list[MacroIndicator] = []
    for indicator in MACRO_INDICATORS:
        points = await get_latest_points(db, indicator.id, limit=2)
        if not points:
            continue

        latest = points[0].value
        change_percent = None
        if len(points) >= 2 and points[1].value != 0:
            change_percent = (latest - points[1].value) / abs(points[1].value) * 100

        indicators.append(
            MacroIndicator(
                id=indicator.id,
                label=indicator.label,
                value=_format_value(indicator, latest),
                change_label=_format_change_label(change_percent),
                sentiment=_sentiment_for(indicator.id, change_percent),
                description=indicator.description,
            )
        )
    return indicators


@router.get("/events", response_model=list[MacroEvent])
def list_events() -> list[MacroEvent]:
    return mock_data.get_macro_events()
