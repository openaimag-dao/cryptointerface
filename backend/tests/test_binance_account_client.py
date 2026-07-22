import httpx
import pytest

from app.services.binance.account_client import BinanceAccountClient


def _client(handler) -> BinanceAccountClient:
    client = BinanceAccountClient(api_key="test-key", api_secret="test-secret")
    client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://fapi.binance.com")
    return client


@pytest.mark.asyncio
async def test_no_api_key_returns_empty_without_a_request():
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, json=[])

    client = BinanceAccountClient(api_key="", api_secret="")
    client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://fapi.binance.com")

    try:
        balances = await client.get_balances()
    finally:
        await client.close()

    assert balances == []
    assert called is False


@pytest.mark.asyncio
async def test_signed_request_includes_timestamp_signature_and_api_key_header():
    seen_params: dict = {}
    seen_headers: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_params.update(dict(request.url.params))
        seen_headers.update(dict(request.headers))
        return httpx.Response(200, json=[])

    client = _client(handler)
    try:
        await client.get_balances()
    finally:
        await client.close()

    assert "timestamp" in seen_params
    assert "recvWindow" in seen_params
    assert "signature" in seen_params
    assert len(seen_params["signature"]) == 64  # hex-encoded SHA256
    assert seen_headers.get("x-mbx-apikey") == "test-key"


@pytest.mark.asyncio
async def test_get_balances_parses_usdt_row():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[
                {
                    "asset": "USDT",
                    "balance": "10000.50",
                    "crossWalletBalance": "10000.50",
                    "crossUnPnl": "125.30",
                    "availableBalance": "9800.00",
                }
            ],
        )

    client = _client(handler)
    try:
        balances = await client.get_balances()
    finally:
        await client.close()

    assert len(balances) == 1
    assert balances[0].asset == "USDT"
    assert balances[0].balance == 10000.50
    assert balances[0].cross_unrealized_pnl == 125.30


@pytest.mark.asyncio
async def test_get_position_risk_parses_signed_amount():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[
                {
                    "symbol": "BTCUSDT",
                    "positionAmt": "-0.5",
                    "entryPrice": "65000",
                    "markPrice": "64000",
                    "unRealizedProfit": "500",
                    "leverage": "10",
                    "updateTime": 1_700_000_000_000,
                }
            ],
        )

    client = _client(handler)
    try:
        positions = await client.get_position_risk()
    finally:
        await client.close()

    assert len(positions) == 1
    assert positions[0].position_amt == -0.5
    assert positions[0].entry_price == 65000.0


@pytest.mark.asyncio
async def test_get_user_trades_parses_fields():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["symbol"] == "ETHUSDT"
        return httpx.Response(
            200,
            json=[
                {
                    "symbol": "ETHUSDT",
                    "id": 1,
                    "side": "SELL",
                    "price": "3500",
                    "qty": "1.0",
                    "realizedPnl": "300",
                    "time": 1_700_000_000_000,
                }
            ],
        )

    client = _client(handler)
    try:
        trades = await client.get_user_trades("ETHUSDT")
    finally:
        await client.close()

    assert len(trades) == 1
    assert trades[0].side == "SELL"
    assert trades[0].realized_pnl == 300.0


@pytest.mark.asyncio
async def test_error_status_raises_binance_account_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"code": -2015, "msg": "Invalid API-key"})

    client = _client(handler)
    try:
        with pytest.raises(Exception, match="Binance account error"):
            await client.get_balances()
    finally:
        await client.close()
