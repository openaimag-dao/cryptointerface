"""REST clients for the macro data providers (see `symbols.py`'s
docstring for why these and not a single unified feed).

All of them degrade the same way as the rest of the app: an unreachable
provider means "no reading this cycle", never a raised exception that
could take down the scheduler — see `service.py`.
"""

import httpx

from app.core.logging import get_logger
from app.utils.retry import retry_async

logger = get_logger(__name__)

RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
FEAR_GREED_BASE_URL = "https://api.alternative.me"
YAHOO_FINANCE_BASE_URL = "https://query1.finance.yahoo.com"
# Yahoo's public chart endpoint rejects a request outright (429, on the
# very first call — not real rate-limiting) unless it looks like it came
# from a browser. This is the one thing standing between "free, keyless"
# and "works" for this endpoint.
YAHOO_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class MacroProviderError(Exception):
    pass


async def fetch_fear_greed_index(timeout: float = 10.0) -> float | None:
    """Crypto Fear & Greed Index, 0-100. Free, keyless, one reading/day
    (the provider itself only updates daily)."""
    async with httpx.AsyncClient(base_url=FEAR_GREED_BASE_URL, timeout=timeout) as client:

        async def _do_request() -> dict:
            response = await client.get("/fng/", params={"limit": 1})
            if response.status_code in RETRYABLE_STATUS_CODES:
                raise MacroProviderError(f"Retryable status {response.status_code} from Fear & Greed API")
            if response.is_error:
                raise MacroProviderError(f"Fear & Greed API error {response.status_code}: {response.text[:200]}")
            return response.json()

        try:
            raw = await retry_async(
                _do_request,
                max_attempts=3,
                base_delay=1.0,
                max_delay=10.0,
                retry_exceptions=(MacroProviderError, httpx.TransportError, httpx.TimeoutException),
            )
        except Exception as exc:  # noqa: BLE001 — a poller cycle skipping one indicator is not fatal
            logger.warning("fear_greed_fetch_failed", extra={"error": str(exc)})
            return None

    data = raw.get("data") or []
    if not data:
        return None
    try:
        return float(data[0]["value"])
    except (KeyError, ValueError, TypeError):
        return None


async def fetch_yahoo_finance_quote(symbol: str, timeout: float = 10.0) -> float | None:
    """Free, keyless quote for an index/commodity/yield via Yahoo
    Finance's public (undocumented, but widely relied on) chart endpoint —
    used because none of DXY/Gold/Silver/WTI/Brent/Dow/S&P 500/NASDAQ
    100/VIX/US 10Y have an official free feed of their own. Returns
    `regularMarketPrice` as-is: for `^TNX` (US 10Y) that's already a plain
    yield (4.72 means 4.72%), for everything else it's the instrument's
    literal quoted price — no unit conversion needed either way."""
    async with httpx.AsyncClient(
        base_url=YAHOO_FINANCE_BASE_URL, timeout=timeout, headers={"User-Agent": YAHOO_USER_AGENT}
    ) as client:

        async def _do_request() -> dict:
            response = await client.get(f"/v8/finance/chart/{symbol}", params={"interval": "1d", "range": "5d"})
            if response.status_code in RETRYABLE_STATUS_CODES:
                raise MacroProviderError(f"Retryable status {response.status_code} from Yahoo Finance")
            if response.is_error:
                raise MacroProviderError(f"Yahoo Finance error {response.status_code}: {response.text[:200]}")
            return response.json()

        try:
            raw = await retry_async(
                _do_request,
                max_attempts=3,
                base_delay=1.0,
                max_delay=10.0,
                retry_exceptions=(MacroProviderError, httpx.TransportError, httpx.TimeoutException),
            )
        except Exception as exc:  # noqa: BLE001 — one skipped indicator, not a poller crash
            logger.warning("yahoo_finance_fetch_failed", extra={"symbol": symbol, "error": str(exc)})
            return None

    try:
        result = raw["chart"]["result"][0]
        return float(result["meta"]["regularMarketPrice"])
    except (KeyError, IndexError, TypeError, ValueError):
        return None
