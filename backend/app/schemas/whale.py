from typing import Literal

from app.schemas.base import CamelModel

WalletType = Literal["EXCHANGE", "UNKNOWN"]
WhaleDirection = Literal["TO_EXCHANGE", "FROM_EXCHANGE"]


class WhaleTransaction(CamelModel):
    id: str
    asset: str
    amount: float
    usd_value: float
    wallet_type: WalletType
    direction: WhaleDirection
    exchange: str | None
    confidence: float
    from_address: str
    to_address: str
    tx_hash: str
    timestamp: str
