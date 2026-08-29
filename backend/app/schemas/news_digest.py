from app.schemas.base import CamelModel


class NewsDigestOut(CamelModel):
    topic: str
    summary: str
    highlights: list[str]
    article_count: int
    generated_at: str
