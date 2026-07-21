"""Deterministic news classifier — no LLM call per article.

A poll cycle can pull dozens of articles across all sources; running each
one through Claude would be slow and turn every poll into a pile of
billed API calls for something that just needs a rough directional read.
Keyword matching is instant, free, and reproducible — the same tradeoff
`app/ai_engine/scoring/`'s modules already make (e.g. `funding.py`'s
fixed point budgets) rather than a learned/sampled model. It's less
nuanced than an LLM read, but transparent and auditable: every score can
be traced back to which words matched.

Confidence reflects how much signal was actually found (keyword hits) —
an article with no matches at all is NEUTRAL with low confidence, not a
confident "nothing's happening" read.
"""

import re
from dataclasses import dataclass

from app.core.config import get_settings

# name/ticker -> the watchlist base asset it refers to, e.g. "bitcoin" -> "BTC".
# Only symbols actually in the watchlist are ever returned by detect_symbols().
_ASSET_ALIASES: dict[str, str] = {
    "bitcoin": "BTC",
    "btc": "BTC",
    "ethereum": "ETH",
    "ether": "ETH",
    "eth": "ETH",
    "solana": "SOL",
    "sol": "SOL",
    "chainlink": "LINK",
    "link": "LINK",
    "dogecoin": "DOGE",
    "doge": "DOGE",
    "binance coin": "BNB",
    "bnb": "BNB",
    "ripple": "XRP",
    "xrp": "XRP",
}

_BULLISH_KEYWORDS = [
    "surge",
    "rally",
    "soar",
    "adoption",
    "inflow",
    "breakout",
    "accumulate",
    "accumulation",
    "partnership",
    "approval",
    "approved",
    "bullish",
    "institutional demand",
    "all-time high",
    "record high",
    "outperform",
]
_BEARISH_KEYWORDS = [
    "crash",
    "hack",
    "exploit",
    "lawsuit",
    "banned",
    "outflow",
    "sell-off",
    "selloff",
    "bearish",
    "crackdown",
    "delist",
    "delisting",
    "insolvency",
    "bankruptcy",
    "plunge",
    "collapse",
    "fraud",
]
_HIGH_IMPACT_KEYWORDS = [
    "sec",
    "regulation",
    "regulatory",
    "etf",
    "hack",
    "bankruptcy",
    "federal reserve",
    "interest rate",
    "lawsuit",
    "ban",
]
_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Security": ["hack", "exploit", "breach", "vulnerability"],
    "Regulation": ["sec", "regulation", "regulatory", "lawsuit", "ban", "compliance"],
    "Institutional": ["etf", "institutional", "blackrock", "fidelity"],
    "DeFi": ["defi", "liquidity pool", "yield farm", "dex"],
    "Technology": ["upgrade", "mainnet", "protocol", "layer 2", "rollup"],
}

BASE_IMPACT_SCORE = 30.0
HIGH_IMPACT_POINTS = 15.0
SYMBOL_MENTION_POINTS = 5.0
MAX_SYMBOL_BONUS_COUNT = 3


@dataclass(frozen=True)
class NewsClassification:
    symbols: list[str]
    sentiment: str  # BULLISH | BEARISH | NEUTRAL
    impact_score: float
    category: str
    confidence: float


def _count_hits(text: str, keywords: list[str]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def detect_symbols(text: str) -> list[str]:
    lowered = text.lower()
    watchlist_bases = {sym[:-4] if sym.endswith("USDT") else sym for sym in get_settings().symbol_list}
    found: set[str] = set()
    for alias, ticker in _ASSET_ALIASES.items():
        if ticker not in watchlist_bases:
            continue
        if re.search(rf"\b{re.escape(alias)}\b", lowered):
            found.add(ticker)
    return sorted(found)


def classify(title: str, summary: str) -> NewsClassification:
    text = f"{title} {summary}".lower()

    symbols = detect_symbols(text)
    bullish_hits = _count_hits(text, _BULLISH_KEYWORDS)
    bearish_hits = _count_hits(text, _BEARISH_KEYWORDS)
    high_impact_hits = _count_hits(text, _HIGH_IMPACT_KEYWORDS)

    if bullish_hits > bearish_hits:
        sentiment = "BULLISH"
    elif bearish_hits > bullish_hits:
        sentiment = "BEARISH"
    else:
        sentiment = "NEUTRAL"

    impact_score = min(
        100.0,
        BASE_IMPACT_SCORE
        + high_impact_hits * HIGH_IMPACT_POINTS
        + min(len(symbols), MAX_SYMBOL_BONUS_COUNT) * SYMBOL_MENTION_POINTS,
    )

    category = "Market"
    for candidate_category, keywords in _CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            category = candidate_category
            break

    total_hits = bullish_hits + bearish_hits + high_impact_hits
    confidence = min(100.0, total_hits * 15.0)

    return NewsClassification(
        symbols=symbols,
        sentiment=sentiment,
        impact_score=impact_score,
        category=category,
        confidence=confidence,
    )
