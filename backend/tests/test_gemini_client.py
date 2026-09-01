import pytest

from app.core.config import get_settings
from app.services import gemini_client
from app.services.gemini_client import generate_structured, generate_text


@pytest.fixture(autouse=True)
def _reset_throttle_state(monkeypatch):
    # The real 13s inter-call spacing (and any monotonic timestamp left
    # over from a previous test) would make this file take minutes to
    # run; every test here exercises the retry/parsing logic, not the
    # throttle's actual timing, so keep it a no-op unless a test opts in.
    monkeypatch.setattr(gemini_client, "_MIN_CALL_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr(gemini_client, "_last_call_monotonic", None)
    yield


class _FakeResponse:
    def __init__(self, text: str | None) -> None:
        self.text = text


class _FakeModels:
    def __init__(self, outer: "_FakeAio") -> None:
        self._outer = outer

    async def generate_content(self, **kwargs):
        self._outer.calls.append(kwargs)
        response = self._outer._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class _FakeAio:
    def __init__(self, responses) -> None:
        self._responses = list(responses) if isinstance(responses, list) else [responses]
        self.calls: list[dict] = []
        self.closed = False
        self.models = _FakeModels(self)

    async def aclose(self) -> None:
        self.closed = True


class _FakeClient:
    last_instance: "_FakeClient | None" = None

    def __init__(self, api_key: str, responses) -> None:
        self.api_key = api_key
        self.aio = _FakeAio(responses)
        _FakeClient.last_instance = self


def _fake_client_factory(responses):
    def _make(*, api_key: str) -> _FakeClient:
        return _FakeClient(api_key, responses)

    return _make


def _rate_limit_error(retry_delay: str = "0s"):
    from google.genai import errors

    return errors.ClientError(
        429,
        {
            "error": {
                "code": 429,
                "status": "RESOURCE_EXHAUSTED",
                "message": "quota exceeded",
                "details": [
                    {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": retry_delay},
                ],
            }
        },
    )


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
    fake_error = errors.ClientError(400, {"error": {"message": "bad request"}})
    monkeypatch.setattr(gemini_client.genai, "Client", _fake_client_factory(fake_error))

    result = await generate_structured(system_prompt="sys", user_message="hi", response_schema={"type": "object"})

    assert result is None
    # Not a 429 -> no retry, just the one call.
    assert len(_FakeClient.last_instance.aio.calls) == 1


@pytest.mark.asyncio
async def test_generate_structured_retries_on_rate_limit_then_succeeds(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(
        gemini_client.genai,
        "Client",
        _fake_client_factory([_rate_limit_error(), _FakeResponse('{"title": "ok"}')]),
    )

    result = await generate_structured(system_prompt="sys", user_message="hi", response_schema={"type": "object"})

    assert result == {"title": "ok"}
    assert len(_FakeClient.last_instance.aio.calls) == 2


@pytest.mark.asyncio
async def test_generate_structured_gives_up_after_max_retries(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    responses = [_rate_limit_error() for _ in range(gemini_client._MAX_RETRIES + 1)]
    monkeypatch.setattr(gemini_client.genai, "Client", _fake_client_factory(responses))

    result = await generate_structured(system_prompt="sys", user_message="hi", response_schema={"type": "object"})

    assert result is None
    assert len(_FakeClient.last_instance.aio.calls) == gemini_client._MAX_RETRIES + 1


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


@pytest.mark.asyncio
async def test_generate_text_retries_on_rate_limit_then_succeeds(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(
        gemini_client.genai,
        "Client",
        _fake_client_factory([_rate_limit_error(), _FakeResponse("Hello there")]),
    )

    result = await generate_text(system_prompt="sys", messages=[{"role": "user", "content": "hi"}])

    assert result == "Hello there"
    assert len(_FakeClient.last_instance.aio.calls) == 2


@pytest.mark.asyncio
async def test_throttle_spaces_out_consecutive_calls(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(gemini_client, "_MIN_CALL_INTERVAL_SECONDS", 0.05)
    monkeypatch.setattr(
        gemini_client.genai,
        "Client",
        _fake_client_factory([_FakeResponse("first"), _FakeResponse("second")]),
    )

    import time

    start = time.monotonic()
    await generate_text(system_prompt="sys", messages=[{"role": "user", "content": "hi"}])
    await generate_text(system_prompt="sys", messages=[{"role": "user", "content": "hi"}])
    elapsed = time.monotonic() - start

    assert elapsed >= 0.05
