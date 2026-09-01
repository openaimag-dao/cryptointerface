from app.schemas.base import CamelModel
from app.schemas.market import Sentiment


class EntityOut(CamelModel):
    """One AI-extracted named thing (company/person/cryptocurrency/
    protocol/country/technology) — see app/models/entity.py. `slug`
    links to its /tag/{slug} archive page."""

    name: str
    slug: str
    entity_type: str


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
    ai_summary: str | None
    image_url: str | None
    entities: list[EntityOut] = []


class PortalNewsPage(CamelModel):
    items: list[NewsItem]
    total: int
    limit: int
    offset: int


class EntityNewsPage(CamelModel):
    """Same shape as PortalNewsPage, plus which entity this /tag/{slug}
    archive page is for."""

    entity: EntityOut
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
