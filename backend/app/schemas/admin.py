from app.schemas.base import CamelModel
from app.schemas.news import NewsItem


class AdminNewsPage(CamelModel):
    items: list[NewsItem]
    total: int
    limit: int
    offset: int


class AdminNewsUpdateRequest(CamelModel):
    title: str | None = None
    summary: str | None = None
    category: str | None = None
    portal_topic: str | None = None
    editorial_status: str | None = None


class EditorialStatusCounts(CamelModel):
    counts: dict[str, int]
