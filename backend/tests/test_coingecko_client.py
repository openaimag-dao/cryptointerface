import httpx
import pytest

from app.services.coingecko.candles import fetch_coingecko_fallback_klines, is_supported
from app.services.coingecko.client import CoinGeckoRestClient, CoinGeckoRestError
from app.services.coingecko.symbols import coingecko_id_for_symbol


def _market_row(coin_id: str, price: float) -> dict:
    return {
        "id": coin_id,
        "current_price": price,
        "high_24h": price * 1.02,
        "low_24h": price * 0.98,
        "price_change_percentage_24h": 1.5,
        "total_volume": 1_000_000.0,
    }


@pytest.mark.asyncio
async def test_get_markets_parses_fields():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["ids"] == "bitcoin,ethereum"
        return httpx.Response(200, json=[_market_row("bitcoin", 65000.0), _market_row("ethereum", 1900.0)])

    client = CoinGeckoRestClient()
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://api.coingecko.com/api/v3"
    )

    try:
        markets = await client.get_markets(["bitcoin", "ethereum"])
    finally:
        await client.close()

    assert set(markets.keys()) == {"bitcoin", "ethereum"}
    assert markets["bitcoin"].price == 65000.0
    assert markets["bitcoin"].change_percent_24h == 1.5
    assert markets["ethereum"].price == 1900.0


@pytest.mark.asyncio
async def test_get_markets_empty_input_makes_no_request():
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("should not be called for an empty coin_ids list")

    client = CoinGeckoRestClient()
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://api.coingecko.com/api/v3"
    )

    try:
        markets = await client.get_markets([])
    finally:
        await client.close()

    assert markets == {}


@pytest.mark.asyncio
async def test_get_markets_default_omits_extended_fields():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["price_change_percentage"] == "24h"
        return httpx.Response(200, json=[_market_row("bitcoin", 65000.0)])

    client = CoinGeckoRestClient()
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://api.coingecko.com/api/v3"
    )

    try:
        markets = await client.get_markets(["bitcoin"])
    finally:
        await client.close()

    assert markets["bitcoin"].market_cap is None
    assert markets["bitcoin"].change_percent_7d is None
    assert markets["bitcoin"].change_percent_30d is None


@pytest.mark.asyncio
async def test_get_markets_extended_parses_market_cap_and_7d_30d():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["price_change_percentage"] == "24h,7d,30d"
        row = _market_row("bitcoin", 65000.0)
        row["market_cap"] = 1_300_000_000_000.0
        row["price_change_percentage_7d_in_currency"] = 3.4
        row["price_change_percentage_30d_in_currency"] = -2.1
        return httpx.Response(200, json=[row])

    client = CoinGeckoRestClient()
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://api.coingecko.com/api/v3"
    )

    try:
        markets = await client.get_markets(["bitcoin"], include_extended=True)
    finally:
        await client.close()

    assert markets["bitcoin"].market_cap == 1_300_000_000_000.0
    assert markets["bitcoin"].change_percent_7d == 3.4
    assert markets["bitcoin"].change_percent_30d == -2.1


@pytest.mark.asyncio
async def test_get_ohlc_parses_rows():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[[1_700_000_000_000, 100.0, 101.0, 99.0, 100.5]])

    client = CoinGeckoRestClient()
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://api.coingecko.com/api/v3"
    )

    try:
        candles = await client.get_ohlc("bitcoin", days=1)
    finally:
        await client.close()

    assert len(candles) == 1
    assert candles[0].open == 100.0
    assert candles[0].close == 100.5


@pytest.mark.asyncio
async def test_retries_on_retryable_status_then_succeeds():
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return httpx.Response(429, text="rate limited")
        return httpx.Response(200, json=[_market_row("bitcoin", 65000.0)])

    client = CoinGeckoRestClient()
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://api.coingecko.com/api/v3"
    )

    try:
        markets = await client.get_markets(["bitcoin"])
    finally:
        await client.close()

    assert attempts == 3
    assert markets["bitcoin"].price == 65000.0


@pytest.mark.asyncio
async def test_raises_after_exhausting_retries():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="server error")

    client = CoinGeckoRestClient()
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://api.coingecko.com/api/v3"
    )

    try:
        with pytest.raises(CoinGeckoRestError):
            await client.get_markets(["bitcoin"])
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_ping_returns_false_on_failure_without_raising():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="down")

    client = CoinGeckoRestClient()
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://api.coingecko.com/api/v3"
    )

    try:
        assert await client.ping() is False
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_ping_returns_true_on_success():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"gecko_says": "(V3) To the Moon!"})

    client = CoinGeckoRestClient()
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://api.coingecko.com/api/v3"
    )

    try:
        assert await client.ping() is True
    finally:
        await client.close()


def test_symbol_mapping_covers_default_symbols():
    for symbol in ("BTCUSDT", "ETHUSDT", "SOLUSDT", "LINKUSDT", "DOGEUSDT", "BNBUSDT", "XRPUSDT"):
        assert coingecko_id_for_symbol(symbol) is not None


def test_symbol_mapping_unknown_symbol_returns_none():
    assert coingecko_id_for_symbol("NOTASYMBOLUSDT") is None


def test_is_supported_only_1h_and_4h():
    assert is_supported("1h") is True
    assert is_supported("4h") is True
    for interval in ("1m", "5m", "15m", "1d"):
        assert is_supported(interval) is False


@pytest.mark.asyncio
async def test_fetch_fallback_klines_1h_resamples_to_hourly_spacing():
    def handler(request: httpx.Request) -> httpx.Response:
        # 6 raw 30min bars -> should resample to 3 ~hourly bars.
        base = 1_700_000_000_000
        rows = [[base + i * 1_800_000, 100.0 + i, 101.0 + i, 99.0 + i, 100.5 + i] for i in range(6)]
        return httpx.Response(200, json=rows)

    client = CoinGeckoRestClient()
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://api.coingecko.com/api/v3"
    )

    try:
        klines = await fetch_coingecko_fallback_klines(client, "bitcoin", "1h")
    finally:
        await client.close()

    assert len(klines) == 3
    for i in range(len(klines) - 1):
        assert klines[i + 1].open_time - klines[i].open_time == 3_600_000
    assert all(k.volume == 0.0 for k in klines)


@pytest.mark.asyncio
async def test_fetch_fallback_klines_4h_native_spacing():
    def handler(request: httpx.Request) -> httpx.Response:
        base = 1_700_000_000_000
        rows = [[base + i * 14_400_000, 100.0, 101.0, 99.0, 100.5] for i in range(4)]
        return httpx.Response(200, json=rows)

    client = CoinGeckoRestClient()
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://api.coingecko.com/api/v3"
    )

    try:
        klines = await fetch_coingecko_fallback_klines(client, "bitcoin", "4h")
    finally:
        await client.close()

    assert len(klines) == 4
    for i in range(len(klines) - 1):
        assert klines[i + 1].open_time - klines[i].open_time == 14_400_000


@pytest.mark.asyncio
async def test_fetch_fallback_klines_unsupported_interval_returns_empty():
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("should not be called for an unsupported interval")

    client = CoinGeckoRestClient()
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://api.coingecko.com/api/v3"
    )

    try:
        klines = await fetch_coingecko_fallback_klines(client, "bitcoin", "1m")
    finally:
        await client.close()

    assert klines == []
