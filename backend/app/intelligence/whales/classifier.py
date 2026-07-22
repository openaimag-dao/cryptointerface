"""Classifies a raw transfer against the watched exchange address list
(`addresses.py`): which side (if either) is a known exchange, and
therefore whether this reads as a deposit (`TO_EXCHANGE`, often selling
pressure) or a withdrawal (`FROM_EXCHANGE`, often accumulation).

Deliberately narrow: a transfer between two wallets neither of which is
a known exchange returns `None` — this module has no basis to call it a
"whale" event one way or the other (see `addresses.py`'s docstring for
why unlabeled whale-to-whale accumulation/distribution isn't covered by
this free-tier approach).
"""

from dataclasses import dataclass

from app.intelligence.whales.addresses import EXCHANGE_ADDRESS_TO_NAME

# Both sides being a known exchange (an inter-exchange rebalancing
# transfer) is real but less informative as a sentiment signal than a
# whale-vs-exchange transfer, so it gets a lower confidence.
INTER_EXCHANGE_CONFIDENCE = 40.0
WHALE_EXCHANGE_CONFIDENCE = 90.0


@dataclass(frozen=True)
class ClassifiedTransfer:
    direction: str  # TO_EXCHANGE | FROM_EXCHANGE
    wallet_type: str  # EXCHANGE
    exchange: str
    confidence: float


def classify_transfer(from_address: str, to_address: str) -> ClassifiedTransfer | None:
    to_exchange = EXCHANGE_ADDRESS_TO_NAME.get(to_address.lower())
    from_exchange = EXCHANGE_ADDRESS_TO_NAME.get(from_address.lower())

    if to_exchange and not from_exchange:
        return ClassifiedTransfer(
            direction="TO_EXCHANGE", wallet_type="EXCHANGE", exchange=to_exchange, confidence=WHALE_EXCHANGE_CONFIDENCE
        )
    if from_exchange and not to_exchange:
        return ClassifiedTransfer(
            direction="FROM_EXCHANGE",
            wallet_type="EXCHANGE",
            exchange=from_exchange,
            confidence=WHALE_EXCHANGE_CONFIDENCE,
        )
    if from_exchange and to_exchange:
        return ClassifiedTransfer(
            direction="TO_EXCHANGE", wallet_type="EXCHANGE", exchange=to_exchange, confidence=INTER_EXCHANGE_CONFIDENCE
        )
    return None
