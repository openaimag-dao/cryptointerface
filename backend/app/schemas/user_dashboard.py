from app.schemas.base import CamelModel
from app.schemas.news import NewsItem


class SavedArticlesOut(CamelModel):
    items: list[NewsItem]


class WatchlistOut(CamelModel):
    symbols: list[str]


class WatchlistAddRequest(CamelModel):
    symbol: str
