"""AI News Processing — an original one-sentence summary + named-entity
extraction for one already-ingested article.

Same discipline as app/intelligence/llm/explanation.py and news_digest.py:
the model is given the article's own title + RSS summary as the only
facts, forced through a fixed JSON schema, and the system prompt
explicitly forbids inventing anything not present in the input — it
narrates and extracts, it never adds. Runs on its own schedule
(`run_ai_news_processing`, see app/intelligence/scheduler/tasks.py), not
inline during RSS ingestion — a poll cycle can pull dozens of articles at
once, and blocking it on an LLM call per article would make ingestion
slow and turn every poll into a pile of billed API calls.

Distinct from `app/intelligence/news/classifier.py`'s deterministic
sentiment/symbols/impact_score (kept exactly as-is — nothing here changes
that pipeline) and from `news_digest.py` (which narrates many articles
into one topic-level digest; this narrates and extracts from one article
at a time).
"""

from dataclasses import dataclass

from app.core.config import get_settings
from app.models.news import NewsArticle
from app.services.gemini_client import generate_structured

VALID_ENTITY_TYPES = ("COMPANY", "PERSON", "CRYPTOCURRENCY", "PROTOCOL", "COUNTRY", "TECHNOLOGY")

SYSTEM_PROMPT = (
    "You process one real news article for a public news portal. You will be given its title and a summary "
    "pulled from the original source's RSS feed — both real. Respond with a short original summary in your own "
    "words (not a copy of the input) and a list of named entities mentioned. Every claim and every entity must "
    "be traceable to the given title/summary — do not invent facts, numbers, entities, or events not present in "
    "the input."
)

PROCESSING_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "1-2 sentence original summary in your own words, grounded only in the input.",
        },
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string", "enum": list(VALID_ENTITY_TYPES)},
                },
                "required": ["name", "type"],
            },
            "description": "Companies, people, cryptocurrencies, protocols, countries, or technologies named.",
        },
    },
    "required": ["summary", "entities"],
}


@dataclass(frozen=True)
class ExtractedEntity:
    name: str
    entity_type: str


@dataclass(frozen=True)
class NewsProcessingResult:
    summary: str
    entities: list[ExtractedEntity]


async def build_news_processing(article: NewsArticle) -> NewsProcessingResult | None:
    """Returns None if unconfigured or on an upstream error — the caller
    keeps the article's existing raw `summary` and skips entity linking
    rather than fabricating either, consistent with this codebase's
    fail-open philosophy for optional enrichment."""
    settings = get_settings()
    if not settings.gemini_api_key:
        return None

    result = await generate_structured(
        system_prompt=SYSTEM_PROMPT,
        user_message=f"Title: {article.title}\nSummary: {article.summary}",
        response_schema=PROCESSING_SCHEMA,
        max_output_tokens=512,
    )
    if result is None:
        return None

    raw_entities = result.get("entities", [])
    entities = [
        ExtractedEntity(name=str(e["name"]), entity_type=str(e["type"]))
        for e in raw_entities
        if isinstance(e, dict) and e.get("name") and e.get("type") in VALID_ENTITY_TYPES
    ]
    return NewsProcessingResult(summary=str(result.get("summary", "")), entities=entities)
