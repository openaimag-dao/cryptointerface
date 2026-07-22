"""Registry of RSS sources the News Engine aggregates.

To add a new source: add one `NewsSourceDef` here. Nothing else needs to
change — `service.py` iterates this registry on every poll cycle.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class NewsSourceDef:
    id: str
    name: str
    rss_url: str
    language: str = "en"


NEWS_SOURCES: list[NewsSourceDef] = [
    NewsSourceDef(id="coindesk", name="CoinDesk", rss_url="https://www.coindesk.com/arc/outboundfeeds/rss/"),
    NewsSourceDef(id="cointelegraph", name="Cointelegraph", rss_url="https://cointelegraph.com/rss"),
    NewsSourceDef(id="decrypt", name="Decrypt", rss_url="https://decrypt.co/feed"),
]
