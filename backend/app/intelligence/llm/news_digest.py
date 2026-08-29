"""AI News Digest — narrates a portal topic's recent real headlines.

Same discipline as `app/intelligence/llm/explanation.py`: the model is
given the already-ingested articles (title/source/summary, all real RSS
content classified by the deterministic classifier in
`app/intelligence/news/`) as structured facts and forced, via
`tool_choice`, to respond through a fixed JSON schema. It narrates; it
does not invent — the system prompt explicitly forbids adding facts,
numbers, or events not present in the given articles, and every article
it's allowed to reference is real and was ingested moments to hours ago.

Called on a schedule (`run_news_digest_refresh`), not per page view — see
`app/services/news_digest_repository.py` for why.
"""

from dataclasses import dataclass

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.news_repository import get_latest_news

logger = get_logger(__name__)

NOT_CONFIGURED_SUMMARY = (
    "AI digests aren't configured yet — set ANTHROPIC_API_KEY in backend/.env and restart the backend. "
    "The headlines below are still real, ingested by the News Engine; only this narrated summary is unavailable."
)
UPSTREAM_ERROR_SUMMARY = "Couldn't reach Claude to generate a digest just now. The headlines below are still real."

ARTICLES_PER_DIGEST = 15

SYSTEM_PROMPT = (
    "You narrate a real-time news feed for a public news portal. You will be given a list of recently ingested "
    "article headlines and summaries for one topic — all real, pulled from live RSS feeds moments to hours ago. "
    "Call emit_digest with a short summary of what's happening in this topic right now and 3-5 highlight bullets. "
    "Every claim must be traceable to one of the given articles — do not invent facts, numbers, or events not "
    "present in the input, and do not speculate about anything the articles don't say."
)

DIGEST_TOOL = {
    "name": "emit_digest",
    "description": "Emit a narrated digest of the given topic's recent real headlines.",
    "input_schema": {
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
    },
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
    if not settings.anthropic_api_key:
        return _fallback_digest(topic, len(articles), NOT_CONFIGURED_SUMMARY)

    facts = _build_articles_payload(articles)

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    try:
        response = await client.messages.create(
            model=settings.anthropic_chat_model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=[DIGEST_TOOL],
            tool_choice={"type": "tool", "name": "emit_digest"},
            messages=[{"role": "user", "content": f"Recent {topic} articles:\n{facts}"}],
        )
    except anthropic.APIError:
        logger.warning("news_digest_upstream_error", extra={"topic": topic}, exc_info=True)
        return _fallback_digest(topic, len(articles), UPSTREAM_ERROR_SUMMARY)
    finally:
        await client.close()

    tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
    if not tool_use_blocks:
        return _fallback_digest(topic, len(articles), UPSTREAM_ERROR_SUMMARY)

    tool_input = tool_use_blocks[0].input
    return NewsDigestResult(
        topic=topic,
        summary=str(tool_input.get("summary", "")),
        highlights=list(tool_input.get("highlights", [])),
        article_count=len(articles),
    )
