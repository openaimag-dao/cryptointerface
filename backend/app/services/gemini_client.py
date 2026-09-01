"""Shared async Gemini client — the one "how do I get a fact/structured
response out of an LLM" seam every AI-powered feature in this app goes
through (chat, translation, digest, processing, explanation). Gemini
replaced Anthropic Claude as the provider here specifically because it has
a real free tier (Google AI Studio, no card required) that this app's
actual call volume fits inside; Anthropic/OpenAI don't offer one for a
continuously-running service. Each call site's own prompt/schema/fallback
logic is unchanged by this — only the provider plumbing moved.

Degrades the same way every other optional integration in this app does:
no key configured, or an upstream error, returns `None` — never raises —
so every caller's existing fail-open fallback (a clearly-labeled message,
or silently skipping the enrichment) keeps working unchanged.

The free tier's real limit (confirmed live, not documented anywhere
obvious) is 5 requests/minute *per model per project* — easy to blow
through, since every scheduler in app/intelligence/scheduler/tasks.py
calls this module in a plain per-item loop with no delay between calls,
and several of them start their first cycle at the same moment on
startup. Two independent mitigations live here, at the shared seam,
rather than sprinkled across every call site:

1. `_throttle()` — a process-wide minimum spacing between outbound
   Gemini calls (module-level, so it applies across every caller:
   schedulers, the chat endpoint, everything). Keeps normal operation
   under quota instead of relying on 429s to self-regulate.
2. `_call_with_retry()` — a small bounded retry for the 429s that still
   happen anyway (e.g. right after startup, before the throttle has
   "caught up", or a burst of concurrent chat requests), honoring the
   server's own suggested `retryDelay` from the RetryInfo error detail
   instead of guessing.
"""

import asyncio
import json
import time

from google import genai
from google.genai import errors, types

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Free tier: 5 requests/minute/model/project -> one request every 12s
# sustainable. A little headroom above that so we don't ride the exact
# edge of the window.
_MIN_CALL_INTERVAL_SECONDS = 13.0
_MAX_RETRIES = 2
_DEFAULT_RETRY_DELAY_SECONDS = 15.0
_MAX_RETRY_DELAY_SECONDS = 30.0

_throttle_lock = asyncio.Lock()
_last_call_monotonic: float | None = None


async def _throttle() -> None:
    """Blocks until at least `_MIN_CALL_INTERVAL_SECONDS` have passed since
    the last Gemini call *started*, across every caller in the process."""
    global _last_call_monotonic
    async with _throttle_lock:
        now = time.monotonic()
        if _last_call_monotonic is not None:
            wait = _MIN_CALL_INTERVAL_SECONDS - (now - _last_call_monotonic)
            if wait > 0:
                await asyncio.sleep(wait)
        _last_call_monotonic = time.monotonic()


def _retry_delay_seconds(error: errors.APIError) -> float:
    """Reads the server-suggested backoff (RetryInfo.retryDelay) out of a
    429's error body instead of guessing one. Falls back to a fixed
    default when the shape isn't what's expected."""
    try:
        details = error.details.get("error", {}).get("details", [])
        for entry in details:
            if entry.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                raw = str(entry.get("retryDelay", ""))
                if raw.endswith("s"):
                    return min(float(raw[:-1]), _MAX_RETRY_DELAY_SECONDS)
    except (AttributeError, TypeError, ValueError):
        pass
    return _DEFAULT_RETRY_DELAY_SECONDS


async def _call_with_retry(client: genai.Client, **kwargs):
    """Runs one `generate_content` call, retrying a bounded number of times
    only on 429 RESOURCE_EXHAUSTED (the free-tier rate limit) — any other
    upstream error is not retried, it's handled by the caller's existing
    except-and-return-None fallback."""
    for attempt in range(_MAX_RETRIES + 1):
        await _throttle()
        try:
            return await client.aio.models.generate_content(**kwargs)
        except errors.ClientError as error:
            if error.code != 429 or attempt == _MAX_RETRIES:
                raise
            delay = _retry_delay_seconds(error)
            logger.warning(
                "gemini_rate_limited_retrying",
                extra={"attempt": attempt + 1, "delay_seconds": delay},
            )
            await asyncio.sleep(delay)
    raise AssertionError("unreachable")  # loop always returns or raises


async def generate_structured(
    *,
    system_prompt: str,
    user_message: str,
    response_schema: dict,
    max_output_tokens: int = 1024,
) -> dict | None:
    """Forces a JSON response through `response_schema` — Gemini's native
    structured-output mode, the equivalent of Claude's forced
    `tool_choice`. `response_schema` is a plain JSON-schema dict (the same
    shape every call site already had for its Claude tool's
    `input_schema` — Gemini's schema subset is compatible for the
    object/string/array/enum shapes this app uses)."""
    settings = get_settings()
    if not settings.gemini_api_key:
        return None

    client = genai.Client(api_key=settings.gemini_api_key)
    try:
        response = await _call_with_retry(
            client,
            model=settings.gemini_model,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=response_schema,
                max_output_tokens=max_output_tokens,
            ),
        )
    except errors.APIError:
        logger.warning("gemini_generate_structured_upstream_error", exc_info=True)
        return None
    finally:
        await client.aio.aclose()

    if not response.text:
        return None
    try:
        parsed = json.loads(response.text)
    except json.JSONDecodeError:
        logger.warning("gemini_generate_structured_invalid_json")
        return None
    return parsed if isinstance(parsed, dict) else None


async def generate_text(
    *,
    system_prompt: str,
    messages: list[dict],
    max_output_tokens: int = 1024,
) -> str | None:
    """Plain multi-turn text chat (the AI Chat assistant's use case) — no
    forced schema. `messages` is `[{"role": "user"|"assistant", "content":
    str}, ...]`, the same shape callers already built for Claude."""
    settings = get_settings()
    if not settings.gemini_api_key:
        return None

    contents = [
        types.Content(role="model" if m["role"] == "assistant" else "user", parts=[types.Part(text=m["content"])])
        for m in messages
    ]

    client = genai.Client(api_key=settings.gemini_api_key)
    try:
        response = await _call_with_retry(
            client,
            model=settings.gemini_model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_output_tokens,
            ),
        )
    except errors.APIError:
        logger.warning("gemini_generate_text_upstream_error", exc_info=True)
        return None
    finally:
        await client.aio.aclose()

    return response.text or None
