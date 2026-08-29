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
    portal_topic: str | None


class PortalNewsPage(CamelModel):
    items: list[NewsItem]
    total: int
    limit: int
    offset: int


class NewsEventOut(CamelModel):
    """Multi-source coverage of one real-world event, grouped by
    app/intelligence/news/dedup.py. `articles` is ordered earliest-first;
    the first entry is the primary/anchor article."""

    id: str
    title: str
    portal_topic: str | None
    importance_score: float
    articles: list[NewsItem]
