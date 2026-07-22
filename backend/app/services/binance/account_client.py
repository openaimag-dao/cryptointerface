"""Async REST client for Binance USDT-M Futures **account** endpoints —
balance, open positions, and realized-PnL income history. Signed requests
only; `rest_client.py` stays public-market-data-only on purpose (see its
docstring).

Degrades the same way as the rest of the app's optional integrations
(Etherscan, Alpha Vantage — see `app/intelligence/whales/providers.py`):
no API key configured means every method returns an empty list rather
than raising, so a caller with a `settings.binance_api_key` check can
skip calling this at all, and a caller without one still fails safe.
"""

import hashlib
import hmac
import time
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.utils.retry import retry_async

logger = get_logger(__name__)
settings = get_settings()

RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
RECV_WINDOW_MS = 5000


class BinanceAccountError(Exception):
    pass


@dataclass(frozen=True)
class AccountBalance:
    asset: str
    balance: float
    cross_wallet_balance: float
    cross_unrealized_pnl: float
    available_balance: float


@dataclass(frozen=True)
class PositionRisk:
    symbol: str
    position_amt: float  # signed: positive = LONG, negative = SHORT
    entry_price: float
    mark_price: float
    unrealized_profit: float
    leverage: int
    update_time: int  # unix ms


@dataclass(frozen=True)
class IncomeRecord:
    symbol: str
    income_type: str
    income: float
    time: int  # unix ms
    trade_id: str


def _parse_balance(raw: dict) -> AccountBalance:
    return AccountBalance(
        asset=raw["asset"],
        balance=float(raw["balance"]),
        cross_wallet_balance=float(raw["crossWalletBalance"]),
        cross_unrealized_pnl=float(raw["crossUnPnl"]),
        available_balance=float(raw["availableBalance"]),
    )


def _parse_position(raw: dict) -> PositionRisk:
    return PositionRisk(
        symbol=raw["symbol"],
        position_amt=float(raw["positionAmt"]),
        entry_price=float(raw["entryPrice"]),
        mark_price=float(raw["markPrice"]),
        unrealized_profit=float(raw["unRealizedProfit"]),
        leverage=int(raw["leverage"]),
        update_time=int(raw["updateTime"]),
    )


def _parse_income(raw: dict) -> IncomeRecord:
    return IncomeRecord(
        symbol=raw.get("symbol", ""),
        income_type=raw["incomeType"],
        income=float(raw["income"]),
        time=int(raw["time"]),
        trade_id=raw.get("tradeId", ""),
    )


@dataclass(frozen=True)
class UserTrade:
    symbol: str
    id: int
    side: str  # "BUY" | "SELL"
    price: float  # this fill's own price
    qty: float
    realized_pnl: float  # 0 for a fill that opened/added to a position, non-zero for one that closed/reduced it
    time: int  # unix ms


def _parse_user_trade(raw: dict) -> UserTrade:
    return UserTrade(
        symbol=raw["symbol"],
        id=int(raw["id"]),
        side=raw["side"],
        price=float(raw["price"]),
        qty=float(raw["qty"]),
        realized_pnl=float(raw["realizedPnl"]),
        time=int(raw["time"]),
    )


class BinanceAccountClient:
    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        base_url: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._api_key = api_key if api_key is not None else settings.binance_api_key
        self._api_secret = api_secret if api_secret is not None else settings.binance_api_secret
        self._client = httpx.AsyncClient(base_url=base_url or settings.binance_rest_base_url, timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "BinanceAccountClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()

    def _sign(self, params: dict) -> dict:
        signed = {**params, "timestamp": int(time.time() * 1000), "recvWindow": RECV_WINDOW_MS}
        query = urlencode(signed)
        signature = hmac.new(self._api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        signed["signature"] = signature
        return signed

    async def _signed_get(self, path: str, params: dict | None = None) -> dict | list:
        if not self._api_key or not self._api_secret:
            return []

        async def _do_request() -> dict | list:
            response = await self._client.get(
                path,
                params=self._sign(params or {}),
                headers={"X-MBX-APIKEY": self._api_key},
            )
            if response.status_code in RETRYABLE_STATUS_CODES:
                raise BinanceAccountError(f"Retryable status {response.status_code} from {path}")
            if response.is_error:
                raise BinanceAccountError(
                    f"Binance account error {response.status_code} from {path}: {response.text[:200]}"
                )
            return response.json()

        return await retry_async(
            _do_request,
            max_attempts=3,
            base_delay=0.5,
            max_delay=5.0,
            retry_exceptions=(BinanceAccountError, httpx.TransportError, httpx.TimeoutException),
        )

    async def get_balances(self) -> list[AccountBalance]:
        raw = await self._signed_get("/fapi/v2/balance")
        assert isinstance(raw, list)
        return [_parse_balance(row) for row in raw]

    async def get_position_risk(self) -> list[PositionRisk]:
        raw = await self._signed_get("/fapi/v2/positionRisk")
        assert isinstance(raw, list)
        return [_parse_position(row) for row in raw]

    async def get_income_history(self, income_type: str = "REALIZED_PNL", limit: int = 100) -> list[IncomeRecord]:
        raw = await self._signed_get("/fapi/v1/income", params={"incomeType": income_type, "limit": limit})
        assert isinstance(raw, list)
        return [_parse_income(row) for row in raw]

    async def get_user_trades(self, symbol: str, limit: int = 50) -> list[UserTrade]:
        raw = await self._signed_get("/fapi/v1/userTrades", params={"symbol": symbol, "limit": limit})
        assert isinstance(raw, list)
        return [_parse_user_trade(row) for row in raw]
