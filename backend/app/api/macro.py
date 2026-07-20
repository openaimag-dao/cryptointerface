from fastapi import APIRouter

from app import mock_data
from app.schemas.macro import MacroEvent, MacroIndicator

router = APIRouter(prefix="/api/macro", tags=["macro"])


@router.get("/indicators", response_model=list[MacroIndicator])
def list_indicators() -> list[MacroIndicator]:
    return mock_data.get_macro_indicators()


@router.get("/events", response_model=list[MacroEvent])
def list_events() -> list[MacroEvent]:
    return mock_data.get_macro_events()
