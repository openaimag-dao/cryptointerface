from typing import Literal

from pydantic import BaseModel

WhaleTxType = Literal["TRANSFER", "DEPOSIT", "WITHDRAWAL", "SWAP"]


class WhaleTransaction(BaseModel):
    id: str
    symbol: str
    type: WhaleTxType
    amount: float
    amount_usd: float
    from_address: str
    to_address: str
    exchange: str | None
    timestamp: str
    tx_hash: str
