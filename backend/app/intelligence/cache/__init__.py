"""Cache key templates + TTLs for the Intelligence Layer.

Reuses `app/core/redis.py`'s generic `cache_get_json`/`cache_set_json` —
this module just centralizes the key naming and TTL choices so
`api/dashboard_intelligence.py` (the highest-traffic endpoint in this
layer — it's what the Dashboard polls) doesn't recompute a full
Sentiment Engine run plus an LLM call on every request.
"""

DASHBOARD_INTELLIGENCE_KEY = "intelligence:dashboard:{symbol}:{interval}"
DASHBOARD_INTELLIGENCE_TTL_SECONDS = 30
