"""Portfolio API — real (see app/services/portfolio_service.py): a single
service Binance USDT-M Futures account's balance/positions/trade history.
Falls back to mock_data.get_portfolio() when BINANCE_API_KEY/SECRET aren't
configured or the account is unreachable — same fail-open pattern as the
CoinGecko fallback for public market data.
"""

from fastapi import APIRouter

from app import mock_data
from app.schemas.portfolio import PortfolioSummary
from app.services.portfolio_service import get_real_portfolio

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("", response_model=PortfolioSummary)
async def get_portfolio() -> PortfolioSummary:
    real = await get_real_portfolio()
    if real is not None:
        return real
    return mock_data.get_portfolio()
