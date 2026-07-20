from fastapi import APIRouter

from app import mock_data
from app.schemas.signal import AiAnalysis, AiSignal

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("", response_model=list[AiSignal])
def list_signals() -> list[AiSignal]:
    return mock_data.get_signals()


@router.get("/analysis/{symbol}", response_model=AiAnalysis)
def get_analysis(symbol: str) -> AiAnalysis:
    return mock_data.get_ai_analysis(symbol.upper())
