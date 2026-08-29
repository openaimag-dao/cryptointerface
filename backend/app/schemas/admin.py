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


class AdminSourceOut(CamelModel):
    id: str
    source_key: str
    name: str
    rss_url: str
    language: str
    default_topic: str
    trust_score: float
    enabled: bool
    auto_publish: bool
    last_fetched_at: str | None
    last_status: str | None
    last_error: str | None
    articles_imported_count: int


class AdminSourceUpdateRequest(CamelModel):
    name: str | None = None
    rss_url: str | None = None
    language: str | None = None
    default_topic: str | None = None
    trust_score: float | None = None
    enabled: bool | None = None
    auto_publish: bool | None = None


class AdminFetchLogOut(CamelModel):
    id: str
    source_id: str
    source_name: str
    status: str
    articles_found: int
    articles_new: int
    error_message: str | None
    duration_ms: int
    created_at: str
