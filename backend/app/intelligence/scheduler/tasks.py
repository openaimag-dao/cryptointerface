"""Background schedulers for the Intelligence Layer — same shape as
`app/tasks/open_interest_poller.py`: a `while not stop_event.is_set()`
loop with a configurable interval, one failure per cycle never crashing
the loop. All intervals are configurable via `app/core/config.py`.
"""

import asyncio

from app.core.config import get_settings
from app.core.logging import get_logger
from app.database.session import AsyncSessionLocal
from app.intelligence.llm.explanation import build_llm_explanation
from app.intelligence.llm.news_digest import build_news_digest
from app.intelligence.llm.news_processing import build_news_processing
from app.intelligence.llm.news_translation import build_news_translation
from app.intelligence.macro.service import fetch_and_persist_macro_snapshot
from app.intelligence.news.service import fetch_and_persist_news
from app.intelligence.sentiment.engine import compute_sentiment
from app.intelligence.whales.service import fetch_and_persist_whale_events
from app.models.ai_processing_log import AIProcessingLog
from app.models.article_translation import SUPPORTED_TRANSLATION_LANGUAGES
from app.services.article_translation_repository import get_articles_missing_translation, upsert_translation
from app.services.entity_repository import link_article_entities
from app.services.llm_repository import insert_llm_report
from app.services.news_digest_repository import insert_news_digest
from app.services.news_repository import get_unprocessed_articles
from app.services.sentiment_repository import insert_sentiment_score

logger = get_logger(__name__)
settings = get_settings()

DEFAULT_INTERVAL = "1h"
PORTAL_TOPICS = ["CRYPTO", "AI", "BLOCKCHAIN", "INNOVATION"]


async def _wait_or_stop(stop_event: asyncio.Event, interval_seconds: float) -> None:
    try:
        await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
    except TimeoutError:
        pass  # normal: just means it's time to run again


async def run_macro_poller(stop_event: asyncio.Event | None = None) -> None:
    stop_event = stop_event or asyncio.Event()
    while not stop_event.is_set():
        try:
            async with AsyncSessionLocal() as db:
                await fetch_and_persist_macro_snapshot(db)
        except Exception:  # noqa: BLE001 — one bad cycle must not kill the poller
            logger.warning("macro_poll_cycle_failed", exc_info=True)
        await _wait_or_stop(stop_event, settings.macro_poll_interval_seconds)


async def run_news_poller(stop_event: asyncio.Event | None = None) -> None:
    stop_event = stop_event or asyncio.Event()
    while not stop_event.is_set():
        try:
            async with AsyncSessionLocal() as db:
                await fetch_and_persist_news(db)
        except Exception:  # noqa: BLE001 — one bad cycle must not kill the poller
            logger.warning("news_poll_cycle_failed", exc_info=True)
        await _wait_or_stop(stop_event, settings.news_poll_interval_seconds)


async def run_whale_poller(stop_event: asyncio.Event | None = None) -> None:
    stop_event = stop_event or asyncio.Event()
    while not stop_event.is_set():
        try:
            async with AsyncSessionLocal() as db:
                await fetch_and_persist_whale_events(db)
        except Exception:  # noqa: BLE001 — one bad cycle must not kill the poller
            logger.warning("whale_poll_cycle_failed", exc_info=True)
        await _wait_or_stop(stop_event, settings.whale_poll_interval_seconds)


async def run_sentiment_recompute(stop_event: asyncio.Event | None = None) -> None:
    stop_event = stop_event or asyncio.Event()
    while not stop_event.is_set():
        for symbol in settings.symbol_list:
            try:
                async with AsyncSessionLocal() as db:
                    result = await compute_sentiment(db, symbol, DEFAULT_INTERVAL)
                    if result is not None:
                        await insert_sentiment_score(db, result)
            except Exception:  # noqa: BLE001 — one symbol failing must not stop the others
                logger.warning("sentiment_recompute_failed", extra={"symbol": symbol}, exc_info=True)
        await _wait_or_stop(stop_event, settings.sentiment_recompute_interval_seconds)


async def run_llm_explanation_refresh(stop_event: asyncio.Event | None = None) -> None:
    """Only refreshes `LLM_EXPLANATION_ANCHOR_SYMBOL` — this feeds the
    Dashboard Intelligence Card's cached "latest explanation" without
    calling Claude on every dashboard poll. `/api/llm/explanation/{symbol}`
    itself still computes live for whatever symbol is requested."""
    stop_event = stop_event or asyncio.Event()
    symbol = settings.llm_explanation_anchor_symbol
    while not stop_event.is_set():
        try:
            async with AsyncSessionLocal() as db:
                explanation = await build_llm_explanation(db, symbol, DEFAULT_INTERVAL)
                if explanation is not None:
                    await insert_llm_report(db, explanation)
        except Exception:  # noqa: BLE001
            logger.warning("llm_explanation_refresh_failed", extra={"symbol": symbol}, exc_info=True)
        await _wait_or_stop(stop_event, settings.llm_explanation_interval_seconds)


async def run_news_digest_refresh(stop_event: asyncio.Event | None = None) -> None:
    """Refreshes the AI-narrated digest for every portal topic. One bad
    topic (e.g. no articles ingested yet) must not stop the others — same
    per-item try/except shape as `run_sentiment_recompute`."""
    stop_event = stop_event or asyncio.Event()
    while not stop_event.is_set():
        for topic in PORTAL_TOPICS:
            try:
                async with AsyncSessionLocal() as db:
                    digest = await build_news_digest(db, topic)
                    if digest is not None:
                        await insert_news_digest(db, digest)
            except Exception:  # noqa: BLE001 — one topic failing must not stop the others
                logger.warning("news_digest_refresh_failed", extra={"topic": topic}, exc_info=True)
        await _wait_or_stop(stop_event, settings.news_digest_interval_seconds)


async def run_ai_news_processing(stop_event: asyncio.Event | None = None) -> None:
    """Backfills `NewsArticle.ai_summary` + entity links for recently-
    ingested articles, oldest-missing-first, `AI_PROCESSING_BATCH_SIZE`
    at a time. No-ops entirely (no batch fetch, no per-article logging)
    when ANTHROPIC_API_KEY isn't configured — same fail-open shape as
    every other Sprint 4 provider, just checked once per cycle instead of
    once per article to avoid log noise when the feature is simply off."""
    stop_event = stop_event or asyncio.Event()
    while not stop_event.is_set():
        if not settings.anthropic_api_key:
            await _wait_or_stop(stop_event, settings.ai_processing_interval_seconds)
            continue

        try:
            async with AsyncSessionLocal() as db:
                articles = await get_unprocessed_articles(db, limit=settings.ai_processing_batch_size)
                for article in articles:
                    try:
                        result = await build_news_processing(article)
                        if result is None:
                            db.add(AIProcessingLog(article_id=article.id, stage="summary", status="ERROR"))
                            await db.commit()
                            continue
                        article.ai_summary = result.summary
                        await db.commit()
                        await link_article_entities(db, article.id, result.entities)
                        db.add(AIProcessingLog(article_id=article.id, stage="summary", status="SUCCESS"))
                        await db.commit()
                    except Exception:  # noqa: BLE001 — one article failing must not stop the batch
                        logger.warning(
                            "news_processing_article_failed", extra={"article_id": article.id}, exc_info=True
                        )
        except Exception:  # noqa: BLE001 — one bad cycle must not kill the poller
            logger.warning("news_processing_cycle_failed", exc_info=True)
        await _wait_or_stop(stop_event, settings.ai_processing_interval_seconds)


async def run_news_translation(stop_event: asyncio.Event | None = None) -> None:
    """Backfills `ArticleTranslation` rows for recently-published
    articles, one language at a time, `TRANSLATION_BATCH_SIZE` articles
    per language per cycle — same "drain the backlog gradually,
    oldest-missing-first" shape as `run_ai_news_processing`. No-ops
    entirely when ANTHROPIC_API_KEY isn't configured, same fail-open
    reasoning as every other optional-enrichment scheduler here."""
    stop_event = stop_event or asyncio.Event()
    while not stop_event.is_set():
        if not settings.anthropic_api_key:
            await _wait_or_stop(stop_event, settings.translation_interval_seconds)
            continue

        for language in SUPPORTED_TRANSLATION_LANGUAGES:
            try:
                async with AsyncSessionLocal() as db:
                    articles = await get_articles_missing_translation(
                        db, language, limit=settings.translation_batch_size
                    )
                    for article in articles:
                        try:
                            result = await build_news_translation(article, language)
                            if result is None:
                                continue
                            await upsert_translation(db, article.id, language, result.title, result.summary)
                        except Exception:  # noqa: BLE001 — one article failing must not stop the batch
                            logger.warning(
                                "news_translation_article_failed",
                                extra={"article_id": article.id, "language": language},
                                exc_info=True,
                            )
            except Exception:  # noqa: BLE001 — one bad cycle must not kill the poller
                logger.warning("news_translation_cycle_failed", extra={"language": language}, exc_info=True)
        await _wait_or_stop(stop_event, settings.translation_interval_seconds)
