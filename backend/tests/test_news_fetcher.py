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
    assert entries[0].image_url is None  # no media:content/enclosure in this fixture


IMAGE_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">
<channel>
  <title>Test Feed</title>
  <item>
    <title>Media content article</title>
    <description>Has a media:content image.</description>
    <link>https://example.com/media-content</link>
    <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
    <media:content url="https://cdn.example.com/media-content.jpg" medium="image" />
  </item>
  <item>
    <title>Media thumbnail article</title>
    <description>Has a media:thumbnail image.</description>
    <link>https://example.com/media-thumbnail</link>
    <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
    <media:thumbnail url="https://cdn.example.com/media-thumbnail.jpg" />
  </item>
  <item>
    <title>Enclosure article</title>
    <description>Has a plain enclosure image.</description>
    <link>https://example.com/enclosure</link>
    <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
    <enclosure url="https://cdn.example.com/enclosure.jpg" type="image/jpeg" length="1000" />
  </item>
  <item>
    <title>No image article</title>
    <description>Nothing image-related at all.</description>
    <link>https://example.com/no-image</link>
    <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
  </item>
</channel>
</rss>
"""


@pytest.mark.asyncio
async def test_fetch_source_extracts_real_image_urls(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=IMAGE_RSS)

    original_client_cls = httpx.AsyncClient

    def fake_async_client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return original_client_cls(*args, **kwargs)

    import app.intelligence.news.fetcher as fetcher_module

    monkeypatch.setattr(fetcher_module.httpx, "AsyncClient", fake_async_client)

    source = NewsSourceDef(id="test", name="Test Source", rss_url="https://example.com/rss")
    entries = await fetch_source(source)

    by_url = {e.url: e for e in entries}
    assert by_url["https://example.com/media-content"].image_url == "https://cdn.example.com/media-content.jpg"
    assert by_url["https://example.com/media-thumbnail"].image_url == "https://cdn.example.com/media-thumbnail.jpg"
    assert by_url["https://example.com/enclosure"].image_url == "https://cdn.example.com/enclosure.jpg"
    assert by_url["https://example.com/no-image"].image_url is None


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


@pytest.mark.asyncio
async def test_fetch_source_keeps_up_to_2000_chars_of_a_long_description(monkeypatch):
    """Regression test: a source that sends a longer excerpt than most
    feeds do must not get silently chopped down to an arbitrarily smaller
    limit — 2000 is NewsArticle.summary's actual column width
    (models/news.py), not a made-up smaller cutoff."""
    long_description = "word " * 500  # 2500 raw chars, well past the old 1000-char cutoff
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>Test Feed</title>
  <item>
    <title>A story with an unusually long RSS excerpt</title>
    <description>{long_description}</description>
    <link>https://example.com/long-summary</link>
    <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
  </item>
</channel>
</rss>
""".encode()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=rss)

    original_client_cls = httpx.AsyncClient

    def fake_async_client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return original_client_cls(*args, **kwargs)

    import app.intelligence.news.fetcher as fetcher_module

    monkeypatch.setattr(fetcher_module.httpx, "AsyncClient", fake_async_client)

    source = NewsSourceDef(id="test", name="Test Source", rss_url="https://example.com/rss")
    entries = await fetch_source(source)

    assert len(entries) == 1
    assert len(entries[0].summary) == 2000
