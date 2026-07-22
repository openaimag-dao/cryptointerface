import httpx
import pytest

from app.intelligence.whales.providers import EtherscanClient


def _patch_client(monkeypatch, handler) -> None:
    original_client_cls = httpx.AsyncClient

    def fake_async_client(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return original_client_cls(*args, **kwargs)

    import app.intelligence.whales.providers as providers_module

    monkeypatch.setattr(providers_module.httpx, "AsyncClient", fake_async_client)


@pytest.mark.asyncio
async def test_get_native_transactions_returns_empty_without_api_key():
    client = EtherscanClient(api_key="")
    result = await client.get_native_transactions("0xabc")
    await client.close()

    assert result == []


@pytest.mark.asyncio
async def test_get_native_transactions_parses_result_list(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "1", "message": "OK", "result": [{"hash": "0x1"}]})

    _patch_client(monkeypatch, handler)

    client = EtherscanClient(api_key="test-key")
    result = await client.get_native_transactions("0xabc")
    await client.close()

    assert result == [{"hash": "0x1"}]


@pytest.mark.asyncio
async def test_get_native_transactions_no_transactions_found_is_empty_not_error(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "0", "message": "No transactions found", "result": []})

    _patch_client(monkeypatch, handler)

    client = EtherscanClient(api_key="test-key")
    result = await client.get_native_transactions("0xabc")
    await client.close()

    assert result == []


@pytest.mark.asyncio
async def test_get_native_transactions_real_error_returns_empty_and_does_not_raise(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "0", "message": "NOTOK", "result": "Invalid API Key"})

    _patch_client(monkeypatch, handler)

    client = EtherscanClient(api_key="bad-key")
    result = await client.get_native_transactions("0xabc")
    await client.close()

    assert result == []


@pytest.mark.asyncio
async def test_get_token_transactions_passes_contract_address(monkeypatch):
    captured_params = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_params.update(dict(request.url.params))
        return httpx.Response(200, json={"status": "1", "message": "OK", "result": []})

    _patch_client(monkeypatch, handler)

    client = EtherscanClient(api_key="test-key")
    await client.get_token_transactions("0xabc", "0xcontract")
    await client.close()

    assert captured_params["action"] == "tokentx"
    assert captured_params["contractaddress"] == "0xcontract"
