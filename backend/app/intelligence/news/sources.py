"""Registry of RSS sources the News Engine aggregates.

To add a new source: add one `NewsSourceDef` here. Nothing else needs to
change — `service.py` iterates this registry on every poll cycle.

`default_topic` is the portal-taxonomy fallback (`app/intelligence/news/
classifier.py`'s `classify_portal_topic()`) used when an article's own text
doesn't clearly match a more specific topic's keywords — e.g. a CoinDesk
piece with no AI/blockchain-infra keywords defaults to CRYPTO since that's
what CoinDesk covers, while a TechCrunch AI piece defaults to AI.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class NewsSourceDef:
    id: str
    name: str
    rss_url: str
    language: str = "en"
    default_topic: str = "CRYPTO"


NEWS_SOURCES: list[NewsSourceDef] = [
    # Crypto
    NewsSourceDef(id="coindesk", name="CoinDesk", rss_url="https://www.coindesk.com/arc/outboundfeeds/rss/"),
    NewsSourceDef(id="cointelegraph", name="Cointelegraph", rss_url="https://cointelegraph.com/rss"),
    NewsSourceDef(id="decrypt", name="Decrypt", rss_url="https://decrypt.co/feed"),
    # AI
    NewsSourceDef(
        id="techcrunch-ai",
        name="TechCrunch AI",
        rss_url="https://techcrunch.com/category/artificial-intelligence/feed/",
        default_topic="AI",
    ),
    NewsSourceDef(
        id="venturebeat-ai",
        name="VentureBeat AI",
        rss_url="https://venturebeat.com/category/ai/feed/",
        default_topic="AI",
    ),
    # Blockchain (infra/institutional angle, distinct from CRYPTO's market-news sources)
    NewsSourceDef(id="theblock", name="The Block", rss_url="https://www.theblock.co/rss.xml", default_topic="BLOCKCHAIN"),
    NewsSourceDef(
        id="cryptoslate", name="CryptoSlate", rss_url="https://cryptoslate.com/feed/", default_topic="BLOCKCHAIN"
    ),
    # Innovation (general tech)
    NewsSourceDef(
        id="techcrunch", name="TechCrunch", rss_url="https://techcrunch.com/feed/", default_topic="INNOVATION"
    ),
    NewsSourceDef(id="wired", name="Wired", rss_url="https://www.wired.com/feed/rss", default_topic="INNOVATION"),
]
