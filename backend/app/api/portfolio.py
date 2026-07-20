from fastapi import APIRouter

from app import mock_data
from app.schemas.portfolio import PortfolioSummary

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("", response_model=PortfolioSummary)
def get_portfolio() -> PortfolioSummary:
    return mock_data.get_portfolio()
