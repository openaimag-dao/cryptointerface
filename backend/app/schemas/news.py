from pydantic import BaseModel

from app.schemas.market import Sentiment


class NewsItem(BaseModel):
    id: str
    title: str
    summary: str
    source: str
    published_at: str
    sentiment: Sentiment
    tags: list[str]
    url: str
