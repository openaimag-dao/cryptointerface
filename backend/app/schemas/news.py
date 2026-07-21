from app.schemas.base import CamelModel
from app.schemas.market import Sentiment


class NewsItem(CamelModel):
    id: str
    source: str
    title: str
    summary: str
    published_at: str
    language: str
    symbols: list[str]
    url: str
    impact_score: float
    sentiment: Sentiment
    category: str
