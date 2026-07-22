"""Known exchange hot-wallet addresses (Ethereum mainnet) the Whale
Engine watches for large deposits/withdrawals.

Etherscan's free-tier API has no chain-wide "show me every transfer over
$X" endpoint — it's address-centric (`txlist`/`tokentx` for one address
at a time). So rather than scanning the whole chain, this watches a
curated list of publicly labeled exchange wallets (the same addresses
Etherscan itself tags, and that appear across most public whale-tracking
dashboards) and reads *their* transaction history: a deposit into one of
these = a large holder moving funds onto an exchange (often read as
selling pressure), a withdrawal = funds moving into private custody
(often read as accumulation). See `classifier.py` for how that direction
is derived.

Coverage is inherently limited to assets with a presence on Ethereum:
native ETH transfers, plus ERC-20 tokens for watchlist symbols that have
one (LINK). BTC/SOL/DOGE/XRP have no Ethereum footprint and aren't
covered by this free-tier approach — see `backend/README.md`'s Whale
Engine section.

To add a new source: add one `WatchedAddress` here, or a new entry to
`TOKEN_CONTRACTS` for another ERC-20 watchlist symbol.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class WatchedAddress:
    address: str
    exchange: str


# Publicly labeled exchange hot wallets (Ethereum mainnet) — same
# addresses Etherscan's own "Label Word Cloud" tags, widely republished
# across whale-tracking dashboards. Lower-cased for case-insensitive
# comparison against API responses (Etherscan returns lowercase).
WATCHED_EXCHANGE_ADDRESSES: list[WatchedAddress] = [
    WatchedAddress(address="0x28c6c06298d514db089934071355e5743bf21d60", exchange="Binance"),
    WatchedAddress(address="0x21a31ee1afc51d94c2efccaa2092ad1028285549", exchange="Binance"),
    WatchedAddress(address="0x71660c4005ba85c37ccec55d0c4493e66fe775d3", exchange="Coinbase"),
    WatchedAddress(address="0x503828976d22510aad0201ac7ec88293211d23da", exchange="Coinbase"),
    WatchedAddress(address="0x2910543af39aba0cd09dbb2d50200b3e800a63d2", exchange="Kraken"),
    WatchedAddress(address="0x6cc5f688a315f3dc28a7781717a9a798a59fda7b", exchange="OKX"),
]

EXCHANGE_ADDRESS_TO_NAME: dict[str, str] = {w.address: w.exchange for w in WATCHED_EXCHANGE_ADDRESSES}

# ERC-20 contract addresses for watchlist symbols that have one.
TOKEN_CONTRACTS: dict[str, str] = {
    "LINK": "0x514910771af9ca656af840dff83e8264ecf986ca",
}

# Native-asset symbol for the chain itself (watched via `txlist`, not `tokentx`).
NATIVE_ASSET = "ETH"
