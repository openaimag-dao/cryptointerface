import pytest

from app.core.config import get_settings
from app.services import gemini_client
from app.services.gemini_client import generate_structured, generate_text


class _FakeResponse:
    def __init__(self, text: str | None) -> None:
        self.text = text


class _FakeModels:
    def __init__(self, outer: "_FakeAio") -> None:
        self._outer = outer

    async def generate_content(self, **kwargs):
        self._outer.calls.append(kwargs)
        if isinstance(self._outer._response, Exception):
            raise self._outer._response
        return self._outer._response


class _FakeAio:
    def __init__(self, response: "_FakeResponse | Exception") -> None:
        self._response = response
        self.calls: list[dict] = []
        self.closed = False
        self.models = _FakeModels(self)

    async def aclose(self) -> None:
        self.closed = True


class _FakeClient:
    last_instance: "_FakeClient | None" = None

    def __init__(self, api_key: str, response: _FakeResponse | Exception) -> None:
        self.api_key = api_key
        self.aio = _FakeAio(response)
        _FakeClient.last_instance = self


def _fake_client_factory(response):
    def _make(*, api_key: str) -> _FakeClient:
        return _FakeClient(api_key, response)

    return _make


@pytest.mark.asyncio
async def test_generate_structured_returns_none_without_api_key(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "")

    result = await generate_structured(system_prompt="sys", user_message="hi", response_schema={"type": "object"})

    assert result is None


@pytest.mark.asyncio
async def test_generate_structured_parses_json_response(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(
        gemini_client.genai, "Client", _fake_client_factory(_FakeResponse('{"title": "hi", "summary": "there"}'))
    )

    result = await generate_structured(
        system_prompt="sys", user_message="hi", response_schema={"type": "object"}, max_output_tokens=256
    )

    assert result == {"title": "hi", "summary": "there"}
    assert _FakeClient.last_instance is not None
    assert _FakeClient.last_instance.aio.closed is True


@pytest.mark.asyncio
async def test_generate_structured_returns_none_on_invalid_json(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(gemini_client.genai, "Client", _fake_client_factory(_FakeResponse("not json")))

    result = await generate_structured(system_prompt="sys", user_message="hi", response_schema={"type": "object"})

    assert result is None


@pytest.mark.asyncio
async def test_generate_structured_returns_none_on_empty_response(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(gemini_client.genai, "Client", _fake_client_factory(_FakeResponse(None)))

    result = await generate_structured(system_prompt="sys", user_message="hi", response_schema={"type": "object"})

    assert result is None


@pytest.mark.asyncio
async def test_generate_structured_returns_none_on_upstream_error(monkeypatch):
    from google.genai import errors

    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    fake_error = errors.ClientError(429, {"error": {"message": "rate limited"}})
    monkeypatch.setattr(gemini_client.genai, "Client", _fake_client_factory(fake_error))

    result = await generate_structured(system_prompt="sys", user_message="hi", response_schema={"type": "object"})

    assert result is None


@pytest.mark.asyncio
async def test_generate_text_returns_none_without_api_key(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "")

    result = await generate_text(system_prompt="sys", messages=[{"role": "user", "content": "hi"}])

    assert result is None


@pytest.mark.asyncio
async def test_generate_text_returns_reply_text(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(gemini_client.genai, "Client", _fake_client_factory(_FakeResponse("Hello there")))

    result = await generate_text(
        system_prompt="sys",
        messages=[{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}],
    )

    assert result == "Hello there"
