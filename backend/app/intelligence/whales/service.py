"""Fetches recent transactions for every watched exchange address (native
ETH + any registered ERC-20 tokens), classifies each one, converts to USD
using this app's own live ticker prices (no separate price API needed —
ETH/LINK are already tracked by the Data Engine), filters by
`WHALE_MIN_USD_THRESHOLD`, and persists whatever clears that bar. Called
by the scheduler on `WHALE_POLL_INTERVAL_SECONDS`.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.intelligence.whales.addresses import NATIVE_ASSET, TOKEN_CONTRACTS, WATCHED_EXCHANGE_ADDRESSES
from app.intelligence.whales.classifier import classify_transfer
from app.intelligence.whales.providers import EtherscanClient
from app.services.market_repository import get_market_stat
from app.services.whale_repository import insert_whale_event

logger = get_logger(__name__)
settings = get_settings()

_ASSET_TO_PRICE_SYMBOL: dict[str, str] = {"ETH": "ETHUSDT", "LINK": "LINKUSDT"}


async def _get_price(db: AsyncSession, asset: str) -> float | None:
    symbol = _ASSET_TO_PRICE_SYMBOL.get(asset)
    if symbol is None:
        return None
    stat = await get_market_stat(db, symbol)
    return stat.price if stat is not None else None


async def _persist_transfer(db: AsyncSession, *, asset: str, tx: dict, decimals: int, price: float) -> bool:
    classified = classify_transfer(tx.get("from", ""), tx.get("to", ""))
    if classified is None:
        return False
    try:
        amount = float(tx["value"]) / (10**decimals)
        timestamp = int(tx["timeStamp"])
        tx_hash = tx["hash"]
    except (KeyError, ValueError):
        return False

    usd_value = amount * price
    if usd_value < settings.whale_min_usd_threshold:
        return False

    return await insert_whale_event(
        db,
        asset=asset,
        amount=amount,
        usd_value=usd_value,
        wallet_type=classified.wallet_type,
        direction=classified.direction,
        exchange=classified.exchange,
        confidence=classified.confidence,
        from_address=tx.get("from", ""),
        to_address=tx.get("to", ""),
        tx_hash=tx_hash,
        timestamp=timestamp,
    )


async def fetch_and_persist_whale_events(db: AsyncSession) -> int:
    persisted = 0

    async with EtherscanClient() as client:
        native_price = await _get_price(db, NATIVE_ASSET)
        token_prices = {asset: await _get_price(db, asset) for asset in TOKEN_CONTRACTS}

        for watched in WATCHED_EXCHANGE_ADDRESSES:
            if native_price is not None:
                for tx in await client.get_native_transactions(watched.address):
                    if await _persist_transfer(db, asset=NATIVE_ASSET, tx=tx, decimals=18, price=native_price):
                        persisted += 1

            for asset, contract in TOKEN_CONTRACTS.items():
                price = token_prices.get(asset)
                if price is None:
                    continue
                for tx in await client.get_token_transactions(watched.address, contract):
                    try:
                        decimals = int(tx.get("tokenDecimal", 18))
                    except ValueError:
                        decimals = 18
                    if await _persist_transfer(db, asset=asset, tx=tx, decimals=decimals, price=price):
                        persisted += 1

    logger.info("whale_poll_cycle_complete", extra={"new_events": persisted})
    return persisted
