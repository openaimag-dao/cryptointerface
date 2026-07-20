from fastapi import APIRouter

from app import mock_data
from app.schemas.backtest import BacktestRequest, BacktestResult

router = APIRouter(prefix="/api/backtesting", tags=["backtesting"])


@router.post("/run", response_model=BacktestResult)
def run_backtest(request: BacktestRequest) -> BacktestResult:
    return mock_data.get_backtest_result(request.strategy, request.symbol, request.timeframe)
