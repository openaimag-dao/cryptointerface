"""Fetches + parses each registered RSS source (see `sources.py`).

The HTTP fetch goes through `httpx` with the same `retry_async` pattern
the rest of the app uses (so a slow/down feed can't hang the poller);
`feedparser` then handles the RSS/Atom format quirks and encoding once
given raw bytes — it never does its own network I/O here.
"""

import re
import time
from dataclasses import dataclass

import feedparser
import httpx

from app.core.logging import get_logger
from app.intelligence.news.sources import NewsSourceDef
from app.utils.retry import retry_async

logger = get_logger(__name__)

RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


class NewsFetchError(Exception):
    pass


@dataclass(frozen=True)
class RawNewsEntry:
    source: str
    title: str
    summary: str
    url: str
    published_at: int  # unix seconds
    language: str


def _entry_published_at(entry: object) -> int:
    for field in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, field, None)
        if parsed:
            return int(time.mktime(parsed))
    return int(time.time())


def _clean_summary(raw_html: str) -> str:
    """RSS summaries are often raw HTML — strip tags for plain text."""
    text = _TAG_RE.sub(" ", raw_html)
    return _WHITESPACE_RE.sub(" ", text).strip()[:1000]


async def fetch_source(source: NewsSourceDef, timeout: float = 10.0) -> list[RawNewsEntry]:
    async def _do_request() -> bytes:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(source.rss_url, headers={"User-Agent": "AIMAG-AI-Terminal/1.0"})
            if response.status_code in RETRYABLE_STATUS_CODES:
                raise NewsFetchError(f"Retryable status {response.status_code} from {source.id}")
            if response.is_error:
                raise NewsFetchError(f"{source.id} RSS error {response.status_code}")
            return response.content

    try:
        raw = await retry_async(
            _do_request,
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            retry_exceptions=(NewsFetchError, httpx.TransportError, httpx.TimeoutException),
        )
    except Exception as exc:  # noqa: BLE001 — one dead feed must not stop the others
        logger.warning("news_source_fetch_failed", extra={"source": source.id, "error": str(exc)})
        return []

    parsed = feedparser.parse(raw)
    entries: list[RawNewsEntry] = []
    for entry in parsed.entries:
        title = getattr(entry, "title", None)
        url = getattr(entry, "link", None)
        if not title or not url:
            continue
        summary_html = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
        entries.append(
            RawNewsEntry(
                source=source.name,
                title=title,
                summary=_clean_summary(summary_html),
                url=url,
                published_at=_entry_published_at(entry),
                language=source.language,
            )
        )
    return entries
