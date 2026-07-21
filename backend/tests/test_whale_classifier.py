from app.intelligence.whales.addresses import WATCHED_EXCHANGE_ADDRESSES
from app.intelligence.whales.classifier import (
    INTER_EXCHANGE_CONFIDENCE,
    WHALE_EXCHANGE_CONFIDENCE,
    classify_transfer,
)

_BINANCE = WATCHED_EXCHANGE_ADDRESSES[0].address
_COINBASE = next(w.address for w in WATCHED_EXCHANGE_ADDRESSES if w.exchange == "Coinbase")
_UNKNOWN_WALLET = "0xdeadbeef00000000000000000000000000dead"


def test_classify_transfer_to_exchange_is_deposit():
    result = classify_transfer(from_address=_UNKNOWN_WALLET, to_address=_BINANCE)

    assert result is not None
    assert result.direction == "TO_EXCHANGE"
    assert result.wallet_type == "EXCHANGE"
    assert result.exchange == "Binance"
    assert result.confidence == WHALE_EXCHANGE_CONFIDENCE


def test_classify_transfer_from_exchange_is_withdrawal():
    result = classify_transfer(from_address=_BINANCE, to_address=_UNKNOWN_WALLET)

    assert result is not None
    assert result.direction == "FROM_EXCHANGE"
    assert result.exchange == "Binance"
    assert result.confidence == WHALE_EXCHANGE_CONFIDENCE


def test_classify_transfer_between_two_exchanges_is_lower_confidence():
    result = classify_transfer(from_address=_BINANCE, to_address=_COINBASE)

    assert result is not None
    assert result.direction == "TO_EXCHANGE"
    assert result.confidence == INTER_EXCHANGE_CONFIDENCE


def test_classify_transfer_between_two_unknown_wallets_is_none():
    result = classify_transfer(from_address=_UNKNOWN_WALLET, to_address="0xcafebabe0000000000000000000000000000ff")

    assert result is None


def test_classify_transfer_is_case_insensitive():
    result = classify_transfer(from_address=_UNKNOWN_WALLET, to_address=_BINANCE.upper())

    assert result is not None
    assert result.exchange == "Binance"
