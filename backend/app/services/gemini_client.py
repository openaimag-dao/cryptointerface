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
"""

import json

from google import genai
from google.genai import errors, types

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


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
        response = await client.aio.models.generate_content(
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
        response = await client.aio.models.generate_content(
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
