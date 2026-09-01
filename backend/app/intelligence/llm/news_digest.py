"""AI News Digest — narrates a portal topic's recent real headlines.

Same discipline as `app/intelligence/llm/explanation.py`: the model is
given the already-ingested articles (title/source/summary, all real RSS
content classified by the deterministic classifier in
`app/intelligence/news/`) as structured facts and forced through a fixed
JSON schema. It narrates; it does not invent — the system prompt
explicitly forbids adding facts, numbers, or events not present in the
given articles, and every article it's allowed to reference is real and
was ingested moments to hours ago.

Called on a schedule (`run_news_digest_refresh`), not per page view — see
`app/services/news_digest_repository.py` for why.
"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.services.gemini_client import generate_structured
from app.services.news_repository import get_latest_news

NOT_CONFIGURED_SUMMARY = (
    "AI digests aren't configured yet — set GEMINI_API_KEY in backend/.env and restart the backend. "
    "The headlines below are still real, ingested by the News Engine; only this narrated summary is unavailable."
)
UPSTREAM_ERROR_SUMMARY = "Couldn't reach Gemini to generate a digest just now. The headlines below are still real."

ARTICLES_PER_DIGEST = 15

SYSTEM_PROMPT = (
    "You narrate a real-time news feed for a public news portal. You will be given a list of recently ingested "
    "article headlines and summaries for one topic — all real, pulled from live RSS feeds moments to hours ago. "
    "Respond with a short summary of what's happening in this topic right now and 3-5 highlight bullets. Every "
    "claim must be traceable to one of the given articles — do not invent facts, numbers, or events not present "
    "in the input, and do not speculate about anything the articles don't say."
)

DIGEST_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "2-4 sentence plain-English summary of what's happening in this topic right now.",
        },
        "highlights": {
            "type": "array",
            "items": {"type": "string"},
            "description": "3-5 short highlight bullets, each grounded in one of the given articles.",
        },
    },
    "required": ["summary", "highlights"],
}


@dataclass(frozen=True)
class NewsDigestResult:
    topic: str
    summary: str
    highlights: list[str]
    article_count: int


def _fallback_digest(topic: str, article_count: int, summary: str) -> NewsDigestResult:
    return NewsDigestResult(topic=topic, summary=summary, highlights=[], article_count=article_count)


def _build_articles_payload(articles: list) -> list[dict]:
    return [{"source": a.source, "title": a.title, "summary": a.summary} for a in articles]


async def build_news_digest(db: AsyncSession, topic: str) -> NewsDigestResult | None:
    """Returns None if there are no ingested articles for this topic yet."""
    articles = await get_latest_news(db, limit=ARTICLES_PER_DIGEST, topic=topic)
    if not articles:
        return None

    settings = get_settings()
    if not settings.gemini_api_key:
        return _fallback_digest(topic, len(articles), NOT_CONFIGURED_SUMMARY)

    facts = _build_articles_payload(articles)
    result = await generate_structured(
        system_prompt=SYSTEM_PROMPT,
        user_message=f"Recent {topic} articles:\n{facts}",
        response_schema=DIGEST_SCHEMA,
        max_output_tokens=1024,
    )
    if result is None:
        return _fallback_digest(topic, len(articles), UPSTREAM_ERROR_SUMMARY)

    return NewsDigestResult(
        topic=topic,
        summary=str(result.get("summary", "")),
        highlights=list(result.get("highlights", [])),
        article_count=len(articles),
    )
