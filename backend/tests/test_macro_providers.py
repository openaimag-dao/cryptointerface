import httpx
import pytest

from app.intelligence.macro.providers import AlphaVantageClient, fetch_fear_greed_index
from app.services.coingecko.client import CoinGeckoRestClient


@pytest.mark.asyncio
async def test_fetch_fear_greed_index_parses_value(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/fng/"
        return httpx.Response(200, json={"data": [{"value": "42", "value_classification": "Fear"}]})

    original_client_cls = httpx.AsyncClient

    def fake_async_client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return original_client_cls(*args, **kwargs)

    import app.intelligence.macro.providers as providers_module

    monkeypatch.setattr(providers_module.httpx, "AsyncClient", fake_async_client)

    value = await fetch_fear_greed_index()
    assert value == 42.0


@pytest.mark.asyncio
async def test_fetch_fear_greed_index_returns_none_on_empty_data(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": []})

    original_client_cls = httpx.AsyncClient

    def fake_async_client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return original_client_cls(*args, **kwargs)

    import app.intelligence.macro.providers as providers_module

    monkeypatch.setattr(providers_module.httpx, "AsyncClient", fake_async_client)

    value = await fetch_fear_greed_index()
    assert value is None


@pytest.mark.asyncio
async def test_alpha_vantage_get_etf_daily_close_without_key_returns_none():
    client = AlphaVantageClient(api_key="")
    try:
        value = await client.get_etf_daily_close("UUP")
    finally:
        await client.close()
    assert value is None


@pytest.mark.asyncio
async def test_alpha_vantage_get_etf_daily_close_parses_latest_close():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["function"] == "TIME_SERIES_DAILY"
        assert request.url.params["symbol"] == "UUP"
        return httpx.Response(
            200,
            json={
                "Time Series (Daily)": {
                    "2024-01-01": {"4. close": "27.10"},
                    "2024-01-02": {"4. close": "27.45"},
                }
            },
        )

    client = AlphaVantageClient(api_key="test-key")
    client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://www.alphavantage.co")

    try:
        value = await client.get_etf_daily_close("UUP")
    finally:
        await client.close()

    assert value == 27.45


@pytest.mark.asyncio
async def test_alpha_vantage_get_etf_daily_close_returns_none_on_rate_limit_note():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"Note": "Thank you for using Alpha Vantage! Our standard API..."})

    client = AlphaVantageClient(api_key="test-key")
    client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://www.alphavantage.co")

    try:
        value = await client.get_etf_daily_close("UUP")
    finally:
        await client.close()

    assert value is None


@pytest.mark.asyncio
async def test_alpha_vantage_get_treasury_yield_parses_latest_value():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["function"] == "TREASURY_YIELD"
        assert request.url.params["maturity"] == "10year"
        return httpx.Response(200, json={"data": [{"date": "2024-01-02", "value": "4.05"}]})

    client = AlphaVantageClient(api_key="test-key")
    client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://www.alphavantage.co")

    try:
        value = await client.get_treasury_yield()
    finally:
        await client.close()

    assert value == 4.05


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
