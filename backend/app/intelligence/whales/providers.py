"""Etherscan REST client — free tier, address-centric (see `addresses.py`'s
docstring for why the Whale Engine watches a curated address list rather
than scanning the whole chain). Degrades the same way as the rest of the
app: no API key or an unreachable API means "no data this cycle", never
a raised exception that could take down the scheduler.
"""

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.utils.retry import retry_async

logger = get_logger(__name__)
settings = get_settings()

RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
ETHERSCAN_BASE_URL = "https://api.etherscan.io"
# Etherscan retired the unversioned /api endpoint in favor of a
# chain-parameterized /v2/api — chainid=1 is Ethereum mainnet, the only
# chain this Whale Engine watches (see addresses.py's docstring).
ETHERSCAN_CHAIN_ID = 1


class EtherscanError(Exception):
    pass


class EtherscanClient:
    def __init__(self, api_key: str | None = None, timeout: float = 15.0) -> None:
        self._api_key = api_key if api_key is not None else settings.etherscan_api_key
        self._client = httpx.AsyncClient(base_url=ETHERSCAN_BASE_URL, timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "EtherscanClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()

    async def _get(self, params: dict) -> list[dict]:
        if not self._api_key:
            return []

        async def _do_request() -> list[dict]:
            response = await self._client.get(
                "/v2/api", params={**params, "chainid": ETHERSCAN_CHAIN_ID, "apikey": self._api_key}
            )
            if response.status_code in RETRYABLE_STATUS_CODES:
                raise EtherscanError(f"Retryable status {response.status_code} from Etherscan")
            if response.is_error:
                raise EtherscanError(f"Etherscan error {response.status_code}: {response.text[:200]}")
            body = response.json()
            # Etherscan uses status "0" both for real errors and for the
            # (non-error) "no transactions found" case — only treat it as
            # an error worth retrying/logging when the message says so.
            if body.get("status") == "0" and body.get("message") not in ("No transactions found", "OK"):
                raise EtherscanError(f"Etherscan error: {body.get('result')}")
            result = body.get("result")
            return result if isinstance(result, list) else []

        try:
            return await retry_async(
                _do_request,
                max_attempts=3,
                base_delay=1.0,
                max_delay=10.0,
                retry_exceptions=(EtherscanError, httpx.TransportError, httpx.TimeoutException),
            )
        except Exception as exc:  # noqa: BLE001 — one address failing must not stop the others
            logger.warning("etherscan_fetch_failed", extra={"error": str(exc)})
            return []

    async def get_native_transactions(self, address: str, limit: int = 20) -> list[dict]:
        """Native ETH transfers (`txlist`) — most recent first."""
        return await self._get(
            {
                "module": "account",
                "action": "txlist",
                "address": address,
                "page": 1,
                "offset": limit,
                "sort": "desc",
            }
        )

    async def get_token_transactions(self, address: str, contract_address: str, limit: int = 20) -> list[dict]:
        """ERC-20 token transfers (`tokentx`) for one contract — most recent first."""
        return await self._get(
            {
                "module": "account",
                "action": "tokentx",
                "address": address,
                "contractaddress": contract_address,
                "page": 1,
                "offset": limit,
                "sort": "desc",
            }
        )
