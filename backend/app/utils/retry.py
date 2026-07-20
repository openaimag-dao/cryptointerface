"""Async retry helper with exponential backoff + jitter.

Used to wrap flaky I/O (Binance REST calls, WS connects) without spreading
ad-hoc try/except-sleep loops across the codebase.
"""

import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


async def retry_async(
    func: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 5,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    retry_exceptions: tuple[type[Exception], ...] = (Exception,),
    on_retry: Callable[[int, Exception], None] | None = None,
) -> T:
    """Call `func()`, retrying on `retry_exceptions` with exponential
    backoff + jitter. Re-raises the last exception once attempts are
    exhausted.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            return await func()
        except retry_exceptions as exc:
            if attempt >= max_attempts:
                logger.error(
                    "retry_exhausted",
                    extra={"attempt": attempt, "max_attempts": max_attempts, "error": str(exc)},
                )
                raise

            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            delay = delay * (0.5 + random.random())  # jitter: 0.5x - 1.5x

            if on_retry:
                on_retry(attempt, exc)
            logger.warning(
                "retrying_after_error",
                extra={
                    "attempt": attempt,
                    "max_attempts": max_attempts,
                    "delay_seconds": round(delay, 2),
                    "error": str(exc),
                },
            )
            await asyncio.sleep(delay)


def compute_backoff_delay(attempt: int, base_delay: float, max_delay: float) -> float:
    """Exponential backoff + jitter, for callers that manage their own loop
    (e.g. the WebSocket client's reconnect loop)."""
    delay = min(max_delay, base_delay * (2 ** max(0, attempt - 1)))
    return delay * (0.5 + random.random())
