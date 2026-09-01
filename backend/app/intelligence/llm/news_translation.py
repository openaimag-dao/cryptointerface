"""AI News Translation — translates one already-ingested article's title
and summary into Russian or Kazakh.

Same discipline as news_processing.py and news_digest.py: the model is
given the article's own title + summary as the only facts, forced through
a fixed JSON schema, and the system prompt explicitly forbids adding,
omitting, or embellishing anything — pure translation, not re-reporting.
Runs on its own schedule (`run_news_translation`, see
app/intelligence/scheduler/tasks.py), not inline during RSS ingestion, for
the same reason news_processing.py doesn't: a poll cycle can pull dozens
of articles, and blocking it on an LLM call per article per language
would make ingestion slow and turn every poll into a pile of billed API
calls.
"""

from dataclasses import dataclass

from app.core.config import get_settings
from app.models.news import NewsArticle
from app.services.gemini_client import generate_structured

LANGUAGE_NAMES = {"ru": "Russian", "kk": "Kazakh"}

SYSTEM_PROMPT = (
    "You translate one real news article's title and summary for a public multilingual news portal into the "
    "requested language. Respond with a faithful translation — do not add, omit, embellish, or fabricate any "
    "fact, number, name, or claim not present in the original. This is translation, not re-reporting: preserve "
    "meaning and tone, adapt only what natural, idiomatic phrasing in the target language requires."
)

TRANSLATION_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "The translated title."},
        "summary": {"type": "string", "description": "The translated summary."},
    },
    "required": ["title", "summary"],
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
    if not settings.gemini_api_key or language not in LANGUAGE_NAMES:
        return None

    result = await generate_structured(
        system_prompt=SYSTEM_PROMPT,
        user_message=(
            f"Translate the following into {LANGUAGE_NAMES[language]}.\n\n"
            f"Title: {article.title}\nSummary: {article.summary}"
        ),
        response_schema=TRANSLATION_SCHEMA,
        max_output_tokens=512,
    )
    if result is None:
        return None

    title = str(result.get("title", "")).strip()
    summary = str(result.get("summary", "")).strip()
    if not title or not summary:
        return None
    return NewsTranslationResult(title=title, summary=summary)
