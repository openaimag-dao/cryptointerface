import httpx
import pytest

from app.services.binance.rest_client import BinanceRestClient, BinanceRestError


def _kline_row(open_time: int) -> list:
    return [open_time, "100", "101", "99", "100.5", "10", open_time + 59_999, "1000", 5, "5", "500", "0"]


@pytest.mark.asyncio
async def test_fetch_historical_klines_paginates_backward():
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        limit = int(request.url.params.get("limit", 1500))
        end_time = request.url.params.get("endTime")
        end_time = int(end_time) if end_time else 1_700_100_000_000
        end_time = (end_time // 60_000) * 60_000  # Binance aligns klines to interval boundaries

        # Binance's endTime is inclusive of open_time <= endTime; the last
        # row in the page is exactly at the (interval-aligned) end_time.
        rows = []
        for i in range(limit):
            open_time = end_time - (limit - 1 - i) * 60_000
            rows.append(_kline_row(open_time))
        return httpx.Response(200, json=rows)

    client = BinanceRestClient()
    client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://fapi.binance.com")

    try:
        klines = await client.fetch_historical_klines("BTCUSDT", "1m", total=3200)
    finally:
        await client.close()

    assert len(klines) == 3200
    assert call_count >= 3  # 3200 candles / 1500 per page needs 3 requests
    # Strictly ascending, contiguous 1-minute candles.
    for i in range(len(klines) - 1):
        assert klines[i + 1].open_time - klines[i].open_time == 60_000


@pytest.mark.asyncio
async def test_get_klines_parses_fields():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[_kline_row(1_700_000_000_000)])

    client = BinanceRestClient()
    client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://fapi.binance.com")

    try:
        klines = await client.get_klines("BTCUSDT", "1m", limit=1)
    finally:
        await client.close()

    assert len(klines) == 1
    kline = klines[0]
    assert kline.open == 100.0
    assert kline.high == 101.0
    assert kline.low == 99.0
    assert kline.close == 100.5
    assert kline.volume == 10.0
    assert kline.trades == 5


@pytest.mark.asyncio
async def test_retries_on_retryable_status_then_succeeds():
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return httpx.Response(429, text="rate limited")
        return httpx.Response(200, json={"symbol": "BTCUSDT", "openInterest": "12345.6", "time": 1})

    client = BinanceRestClient()
    client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://fapi.binance.com")

    try:
        result = await client.get_open_interest("BTCUSDT")
    finally:
        await client.close()

    assert attempts == 3
    assert result["symbol"] == "BTCUSDT"


@pytest.mark.asyncio
async def test_raises_after_exhausting_retries():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="server error")

    client = BinanceRestClient()
    client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://fapi.binance.com")

    try:
        with pytest.raises(BinanceRestError):
            await client.get_open_interest("BTCUSDT")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_ping_returns_false_on_failure_without_raising():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="down")

    client = BinanceRestClient()
    client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://fapi.binance.com")

    try:
        assert await client.ping() is False
    finally:
        await client.close()
