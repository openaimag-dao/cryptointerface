import httpx
import pytest

from app.intelligence.news.fetcher import fetch_source
from app.intelligence.news.sources import NewsSourceDef

SAMPLE_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Test Feed</title>
  <item>
    <title>Bitcoin surges past resistance</title>
    <description><![CDATA[<p>Bitcoin <b>rallies</b> on institutional demand.</p>]]></description>
    <link>https://example.com/article-1</link>
    <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
  </item>
  <item>
    <title>Ethereum network upgrade completed</title>
    <description>The upgrade improves scalability.</description>
    <link>https://example.com/article-2</link>
    <pubDate>Tue, 02 Jan 2024 08:30:00 GMT</pubDate>
  </item>
</channel>
</rss>
"""


@pytest.mark.asyncio
async def test_fetch_source_parses_rss_entries(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=SAMPLE_RSS)

    original_client_cls = httpx.AsyncClient

    def fake_async_client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return original_client_cls(*args, **kwargs)

    import app.intelligence.news.fetcher as fetcher_module

    monkeypatch.setattr(fetcher_module.httpx, "AsyncClient", fake_async_client)

    source = NewsSourceDef(id="test", name="Test Source", rss_url="https://example.com/rss")
    entries = await fetch_source(source)

    assert len(entries) == 2
    assert entries[0].title == "Bitcoin surges past resistance"
    assert entries[0].url == "https://example.com/article-1"
    assert "rallies" in entries[0].summary
    assert "<" not in entries[0].summary  # HTML tags stripped
    assert entries[0].source == "Test Source"
    assert entries[0].language == "en"
    assert entries[0].published_at > 0


@pytest.mark.asyncio
async def test_fetch_source_returns_empty_list_on_http_error(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    original_client_cls = httpx.AsyncClient

    def fake_async_client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return original_client_cls(*args, **kwargs)

    import app.intelligence.news.fetcher as fetcher_module

    monkeypatch.setattr(fetcher_module.httpx, "AsyncClient", fake_async_client)

    source = NewsSourceDef(id="test", name="Test Source", rss_url="https://example.com/rss")
    entries = await fetch_source(source)

    assert entries == []
