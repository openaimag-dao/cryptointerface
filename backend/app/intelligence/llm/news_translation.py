"""AI News Translation — translates one already-ingested article's title
and summary into Russian or Kazakh.

Same discipline as news_processing.py and news_digest.py: Claude is given
the article's own title + summary as the only facts, forced (via
`tool_choice`) through a fixed JSON schema, and the system prompt
explicitly forbids adding, omitting, or embellishing anything — pure
translation, not re-reporting. Runs on its own schedule
(`run_news_translation`, see app/intelligence/scheduler/tasks.py), not
inline during RSS ingestion, for the same reason news_processing.py
doesn't: a poll cycle can pull dozens of articles, and blocking it on a
Claude call per article per language would make ingestion slow and turn
every poll into a pile of billed API calls.
"""

from dataclasses import dataclass

import anthropic

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.news import NewsArticle

logger = get_logger(__name__)

LANGUAGE_NAMES = {"ru": "Russian", "kk": "Kazakh"}

SYSTEM_PROMPT = (
    "You translate one real news article's title and summary for a public multilingual news portal into the "
    "requested language. Call emit_translation with a faithful translation — do not add, omit, embellish, or "
    "fabricate any fact, number, name, or claim not present in the original. This is translation, not "
    "re-reporting: preserve meaning and tone, adapt only what natural, idiomatic phrasing in the target "
    "language requires."
)

TRANSLATION_TOOL = {
    "name": "emit_translation",
    "description": "Emit a faithful translation of the given title and summary.",
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "The translated title."},
            "summary": {"type": "string", "description": "The translated summary."},
        },
        "required": ["title", "summary"],
    },
}


@dataclass(frozen=True)
class NewsTranslationResult:
    title: str
    summary: str


async def build_news_translation(article: NewsArticle, language: str) -> NewsTranslationResult | None:
    """Returns None if unconfigured, the language is unsupported, or on
    an upstream error — the caller leaves the article without a
    translation row for this language and the frontend falls back to the
    original English, consistent with this codebase's fail-open
    philosophy for optional enrichment."""
    settings = get_settings()
    if not settings.anthropic_api_key or language not in LANGUAGE_NAMES:
        return None

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    try:
        response = await client.messages.create(
            model=settings.anthropic_chat_model,
            max_tokens=512,
            system=SYSTEM_PROMPT,
            tools=[TRANSLATION_TOOL],
            tool_choice={"type": "tool", "name": "emit_translation"},
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Translate the following into {LANGUAGE_NAMES[language]}.\n\n"
                        f"Title: {article.title}\nSummary: {article.summary}"
                    ),
                }
            ],
        )
    except anthropic.APIError:
        logger.warning(
            "news_translation_upstream_error", extra={"article_id": article.id, "language": language}, exc_info=True
        )
        return None
    finally:
        await client.close()

    tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
    if not tool_use_blocks:
        return None

    tool_input = tool_use_blocks[0].input
    title = str(tool_input.get("title", "")).strip()
    summary = str(tool_input.get("summary", "")).strip()
    if not title or not summary:
        return None
    return NewsTranslationResult(title=title, summary=summary)
