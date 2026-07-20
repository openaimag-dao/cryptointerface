"""Redis cache client.

Caches the hot path: latest prices, funding, open interest, indicator
snapshots, and recent candles — so REST reads and WS fan-out don't have to
hit Postgres on every request.
"""

import json
from typing import Any

from redis.asyncio import ConnectionPool, Redis

from app.core.config import get_settings

settings = get_settings()

_pool = ConnectionPool.from_url(settings.redis_url, decode_responses=True)
redis_client: Redis = Redis(connection_pool=_pool)

# Key prefixes
TICKER_KEY = "ticker:{symbol}"
FUNDING_KEY = "funding:{symbol}"
OPEN_INTEREST_KEY = "open_interest:{symbol}"
INDICATORS_KEY = "indicators:{symbol}:{interval}"
CANDLES_KEY = "candles:{symbol}:{interval}"
ENGINE_STATUS_KEY = "engine:status"


async def cache_set_json(key: str, value: Any, ttl_seconds: int | None = None) -> None:
    await redis_client.set(key, json.dumps(value, default=str), ex=ttl_seconds)


async def cache_get_json(key: str) -> Any | None:
    raw = await redis_client.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def ping() -> bool:
    try:
        return bool(await redis_client.ping())
    except Exception:
        return False


async def close_redis() -> None:
    await redis_client.aclose()
