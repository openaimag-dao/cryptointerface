from fastapi import APIRouter

from app import mock_data
from app.models.whale import WhaleTransaction

router = APIRouter(prefix="/api/whales", tags=["whales"])


@router.get("/transactions", response_model=list[WhaleTransaction])
def list_whale_transactions(count: int = 24) -> list[WhaleTransaction]:
    return mock_data.get_whale_transactions(count)
