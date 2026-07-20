from fastapi import APIRouter

from app import mock_data
from app.schemas.liquidation import LiquidationEvent, LiquidationHeatmapCell

router = APIRouter(prefix="/api/liquidations", tags=["liquidations"])


@router.get("", response_model=list[LiquidationEvent])
def list_liquidations(count: int = 30) -> list[LiquidationEvent]:
    return mock_data.get_liquidations(count)


@router.get("/heatmap", response_model=list[LiquidationHeatmapCell])
def get_heatmap(base_price: float = 64280, count: int = 40) -> list[LiquidationHeatmapCell]:
    return mock_data.get_liquidation_heatmap(base_price, count)
