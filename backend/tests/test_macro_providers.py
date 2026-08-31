import httpx
import pytest

from app.intelligence.macro.providers import fetch_fear_greed_index, fetch_yahoo_finance_quote
from app.services.coingecko.client import CoinGeckoRestClient


def _mock_client_for(monkeypatch, handler) -> None:
    original_client_cls = httpx.AsyncClient

    def fake_async_client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return original_client_cls(*args, **kwargs)

    import app.intelligence.macro.providers as providers_module

    monkeypatch.setattr(providers_module.httpx, "AsyncClient", fake_async_client)


@pytest.mark.asyncio
async def test_fetch_fear_greed_index_parses_value(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/fng/"
        return httpx.Response(200, json={"data": [{"value": "42", "value_classification": "Fear"}]})

    _mock_client_for(monkeypatch, handler)

    value = await fetch_fear_greed_index()
    assert value == 42.0


@pytest.mark.asyncio
async def test_fetch_fear_greed_index_returns_none_on_empty_data(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": []})

    _mock_client_for(monkeypatch, handler)

    value = await fetch_fear_greed_index()
    assert value is None


@pytest.mark.asyncio
async def test_fetch_yahoo_finance_quote_parses_regular_market_price(monkeypatch):
    # `fetch_yahoo_finance_quote` catches every exception from the request
    # (a real provider failure must never propagate), which would also
    # swallow an `assert` failing inside the handler itself — so the
    # request is captured here and checked after the call, outside that
    # exception-handling scope, rather than asserted from within.
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_requests.append(request)
        return httpx.Response(
            200,
            json={
                "chart": {
                    "result": [{"meta": {"symbol": "^DJI", "regularMarketPrice": 53559.99}}],
                    "error": None,
                }
            },
        )

    _mock_client_for(monkeypatch, handler)

    value = await fetch_yahoo_finance_quote("^DJI")

    assert value == 53559.99
    assert len(seen_requests) == 1
    assert seen_requests[0].url.path == "/v8/finance/chart/^DJI"
    assert seen_requests[0].headers["User-Agent"]  # the one thing this endpoint actually requires


@pytest.mark.asyncio
async def test_fetch_yahoo_finance_quote_returns_none_on_empty_result(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"chart": {"result": None, "error": {"description": "Not Found"}}})

    _mock_client_for(monkeypatch, handler)

    value = await fetch_yahoo_finance_quote("NOTASYMBOL")
    assert value is None


@pytest.mark.asyncio
async def test_fetch_yahoo_finance_quote_returns_none_on_error_status(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="Edge: Too Many Requests")

    _mock_client_for(monkeypatch, handler)

    value = await fetch_yahoo_finance_quote("^DJI")
    assert value is None


@pytest.mark.asyncio
async def test_coingecko_get_global_data_parses_btc_dominance():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/global")
        return httpx.Response(200, json={"data": {"market_cap_percentage": {"btc": 54.32, "eth": 17.1}}})

    client = CoinGeckoRestClient()
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://api.coingecko.com/api/v3"
    )

    try:
        value = await client.get_global_data()
    finally:
        await client.close()

    assert value == 54.32
