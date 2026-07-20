from fastapi import APIRouter

from app import mock_data
from app.schemas.news import NewsItem

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("", response_model=list[NewsItem])
def list_news() -> list[NewsItem]:
    return mock_data.get_news()
