"""REST clients for the three macro data providers (see `symbols.py`'s
docstring for why these three and not a single unified feed).

All three degrade the same way as the rest of the app: a missing API key
or an unreachable provider means "no reading this cycle", never a raised
exception that could take down the scheduler — see `service.py`.
"""

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.utils.retry import retry_async

logger = get_logger(__name__)
settings = get_settings()

RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
FEAR_GREED_BASE_URL = "https://api.alternative.me"
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co"


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


class AlphaVantageClient:
    """Alpha Vantage free tier: 25 requests/day, 5/minute (as of writing).
    `service.py`'s poll interval is set with this budget in mind — see
    `MACRO_POLL_INTERVAL_SECONDS` in `app/core/config.py`."""

    def __init__(self, api_key: str | None = None, timeout: float = 15.0) -> None:
        self._api_key = api_key if api_key is not None else settings.alpha_vantage_api_key
        self._client = httpx.AsyncClient(base_url=ALPHA_VANTAGE_BASE_URL, timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AlphaVantageClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()

    async def _get(self, params: dict) -> dict:
        async def _do_request() -> dict:
            response = await self._client.get("/query", params={**params, "apikey": self._api_key})
            if response.status_code in RETRYABLE_STATUS_CODES:
                raise MacroProviderError(f"Retryable status {response.status_code} from Alpha Vantage")
            if response.is_error:
                raise MacroProviderError(f"Alpha Vantage error {response.status_code}: {response.text[:200]}")
            body = response.json()
            # Alpha Vantage returns HTTP 200 even for rate-limit/invalid-key
            # errors, signaled only in the JSON body.
            if "Note" in body or "Information" in body:
                raise MacroProviderError(f"Alpha Vantage rate-limited or misconfigured: {body}")
            if "Error Message" in body:
                raise MacroProviderError(f"Alpha Vantage error: {body['Error Message']}")
            return body

        return await retry_async(
            _do_request,
            max_attempts=2,  # tiny daily quota — don't burn retries on a flaky response
            base_delay=2.0,
            max_delay=10.0,
            retry_exceptions=(MacroProviderError, httpx.TransportError, httpx.TimeoutException),
        )

    async def get_etf_daily_close(self, ticker: str) -> float | None:
        """Most recent daily close for an ETF ticker, used as a liquid
        proxy for indices/commodities with no direct free feed."""
        if not self._api_key:
            return None
        try:
            body = await self._get({"function": "TIME_SERIES_DAILY", "symbol": ticker})
        except Exception as exc:  # noqa: BLE001 — one skipped indicator, not a poller crash
            logger.warning("alpha_vantage_etf_fetch_failed", extra={"ticker": ticker, "error": str(exc)})
            return None

        series = body.get("Time Series (Daily)")
        if not series:
            return None
        latest_date = max(series.keys())
        try:
            return float(series[latest_date]["4. close"])
        except (KeyError, ValueError, TypeError):
            return None

    async def get_treasury_yield(self, maturity: str = "10year") -> float | None:
        if not self._api_key:
            return None
        try:
            body = await self._get({"function": "TREASURY_YIELD", "interval": "daily", "maturity": maturity})
        except Exception as exc:  # noqa: BLE001
            logger.warning("alpha_vantage_treasury_fetch_failed", extra={"error": str(exc)})
            return None

        data = body.get("data") or []
        if not data:
            return None
        try:
            return float(data[0]["value"])
        except (KeyError, ValueError, TypeError):
            return None
