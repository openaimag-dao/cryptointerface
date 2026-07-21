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
from app.intelligence.macro.service import fetch_and_persist_macro_snapshot
from app.intelligence.news.service import fetch_and_persist_news
from app.intelligence.sentiment.engine import compute_sentiment
from app.services.llm_repository import insert_llm_report
from app.services.sentiment_repository import insert_sentiment_score

logger = get_logger(__name__)
settings = get_settings()

DEFAULT_INTERVAL = "1h"


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
