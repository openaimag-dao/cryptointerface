"""Whale Engine (Sprint 4).

Reads the latest whale snapshot for a symbol
(`app/services/whale_repository.py::get_whale_snapshot_for_symbol()`,
populated by `app/intelligence/whales/` — Etherscan-tracked transfers
touching known exchange wallets, see that module's docstring). Unlike
`funding.py`'s contrarian read, this is a direct read: withdrawals from
exchange wallets (`from_exchange_usd`) mean funds are moving into
private custody — read as accumulation, bullish. Deposits into exchange
wallets (`to_exchange_usd`) mean funds are being positioned to sell —
read as distribution, bearish.

Coverage is inherently limited to assets with an Ethereum footprint
(native ETH, LINK) — see `whale_repository.py`'s `SYMBOL_TO_ASSET`. Other
watchlist symbols always see a `None` snapshot and read neutral here,
same as any other Sprint 4 module before its data lands.

This is a new module (Sprint 3 had no whales stub to replace) — it is
wired into `market_score.py`'s `FACTOR_WEIGHTS` at a small weight, and
into the Sentiment Engine's `whales` category.
"""

from app.ai_engine.types import FactorScore, WhaleSnapshot, clamp, make_factor_score

MIN_MEANINGFUL_TOTAL_USD = 250_000.0  # below this, 24h whale activity is too thin to read
MAX_POINTS = 20.0
IMBALANCE_SCALE = 40.0


def score_whales(snapshot: WhaleSnapshot | None) -> FactorScore:
    reasons: list[str] = []
    details: dict[str, float | str | bool | int] = {}

    if snapshot is None or snapshot.event_count == 0:
        reasons.append("No tracked whale activity in the last 24h — neutral, zero-conviction read")
        factor = make_factor_score("whales", 50.0, reasons, details)
        factor.details["whales_score"] = factor.score
        factor.details["whales_direction"] = factor.direction
        factor.details["whales_strength"] = factor.strength
        return factor

    total = snapshot.to_exchange_usd + snapshot.from_exchange_usd
    details["to_exchange_usd_24h"] = snapshot.to_exchange_usd
    details["from_exchange_usd_24h"] = snapshot.from_exchange_usd

    if total < MIN_MEANINGFUL_TOTAL_USD:
        reasons.append(f"Trailing 24h whale activity too thin (${total:,.0f}) to read as a sentiment signal")
        score = 50.0
    else:
        imbalance = (snapshot.from_exchange_usd - snapshot.to_exchange_usd) / total  # +1 all-out .. -1 all-in
        points = clamp(abs(imbalance) * IMBALANCE_SCALE, 0, MAX_POINTS)
        if snapshot.from_exchange_usd > snapshot.to_exchange_usd:
            score = 50.0 + points
            reasons.append(
                f"Exchange withdrawals (${snapshot.from_exchange_usd:,.0f}) outweigh deposits "
                f"(${snapshot.to_exchange_usd:,.0f}) in the trailing 24h — reads as accumulation, bullish"
            )
        else:
            score = 50.0 - points
            reasons.append(
                f"Exchange deposits (${snapshot.to_exchange_usd:,.0f}) outweigh withdrawals "
                f"(${snapshot.from_exchange_usd:,.0f}) in the trailing 24h — reads as distribution, bearish"
            )

    factor = make_factor_score("whales", score, reasons, details)
    factor.details["whales_score"] = factor.score
    factor.details["whales_direction"] = factor.direction
    factor.details["whales_strength"] = factor.strength
    return factor
