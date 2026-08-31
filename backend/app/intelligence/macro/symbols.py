"""Registry of every macro indicator the Macro Engine tracks.

To add a new indicator: add one entry here, then handle its `provider`
value in `providers.py`/`service.py` if it isn't one of the existing
providers. Nothing else needs to change — `/api/macro/indicators` and the
scheduler both iterate this registry.

Every index/commodity/yield here (DXY, Gold, Silver, WTI, Brent, Dow,
S&P 500, NASDAQ 100, VIX, US 10Y) comes from Yahoo Finance's public
`/v8/finance/chart/{symbol}` endpoint — free, keyless, no daily-quota
cliff the way Alpha Vantage's free tier had (this replaced an earlier
Alpha-Vantage-backed version of this registry that tracked ETF proxies
instead of the real instruments, specifically because it needed a key).
See `providers.py::fetch_yahoo_finance_quote` for the one thing that
endpoint does require: a browser-like User-Agent, or Yahoo's edge
rejects the request outright. Fear & Greed and BTC Dominance are a
separate free/keyless pair (`alternative.me`, CoinGecko `/global`).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MacroIndicatorDef:
    id: str
    label: str
    description: str
    provider: str  # "yahoo_finance" | "fear_greed" | "coingecko_global"
    # Yahoo Finance chart symbol (only set when provider == "yahoo_finance")
    yahoo_symbol: str | None = None
    # Whether score_macro() (app/ai_engine/scoring/macro.py) uses this
    # indicator. A few (Silver, Oil, Brent, Dow) are tracked/displayed but
    # have too weak/ambiguous a direct correlation to crypto risk sentiment,
    # or overlap too heavily with an already-scored sibling, to be worth a
    # scoring sub-weight — see that module's docstring.
    used_in_scoring: bool = True


MACRO_INDICATORS: list[MacroIndicatorDef] = [
    MacroIndicatorDef(
        id="dxy",
        label="DXY Dollar Index",
        description="Weaker dollar historically correlates with crypto strength.",
        provider="yahoo_finance",
        yahoo_symbol="DX-Y.NYB",
    ),
    MacroIndicatorDef(
        id="gold",
        label="Gold (COMEX Futures)",
        description="Safe-haven demand alongside BTC's 'digital gold' narrative.",
        provider="yahoo_finance",
        yahoo_symbol="GC=F",
    ),
    MacroIndicatorDef(
        id="silver",
        label="Silver (COMEX Futures)",
        description="Industrial + precious-metal demand; tracked for context, not scored.",
        provider="yahoo_finance",
        yahoo_symbol="SI=F",
        used_in_scoring=False,
    ),
    MacroIndicatorDef(
        id="oil",
        label="Crude Oil - WTI",
        description="Broad inflation/risk-appetite proxy; tracked for context, not scored.",
        provider="yahoo_finance",
        yahoo_symbol="CL=F",
        used_in_scoring=False,
    ),
    MacroIndicatorDef(
        id="sp500",
        label="S&P 500",
        description="Risk-on equities strength tends to correlate with crypto strength.",
        provider="yahoo_finance",
        yahoo_symbol="^GSPC",
    ),
    MacroIndicatorDef(
        id="nasdaq",
        label="NASDAQ 100",
        description="Tech-heavy risk appetite, the most crypto-correlated equity index.",
        provider="yahoo_finance",
        yahoo_symbol="^NDX",
    ),
    MacroIndicatorDef(
        id="dow",
        label="Dow Jones Industrial Average",
        description="Broad blue-chip equities strength; tracked for context, not scored "
        "— overlaps heavily with S&P 500's risk-on signal.",
        provider="yahoo_finance",
        yahoo_symbol="^DJI",
        used_in_scoring=False,
    ),
    MacroIndicatorDef(
        id="brent",
        label="Crude Oil - Brent",
        description="The international oil benchmark alongside WTI; tracked for context, not scored.",
        provider="yahoo_finance",
        yahoo_symbol="BZ=F",
        used_in_scoring=False,
    ),
    MacroIndicatorDef(
        id="vix",
        label="VIX Volatility Index",
        description="Elevated equity fear historically coincides with crypto de-risking.",
        provider="yahoo_finance",
        yahoo_symbol="^VIX",
    ),
    MacroIndicatorDef(
        id="us10y",
        label="US 10Y Yield",
        description="Rising yields raise the opportunity cost of holding non-yielding risk assets.",
        provider="yahoo_finance",
        yahoo_symbol="^TNX",
    ),
    MacroIndicatorDef(
        id="fear_greed",
        label="Crypto Fear & Greed",
        description="Composite crypto-market sentiment index, 0 (extreme fear) - 100 (extreme greed).",
        provider="fear_greed",
    ),
    MacroIndicatorDef(
        id="btc_dominance",
        label="BTC Dominance",
        description="BTC's share of total crypto market cap — rising dominance often means alt weakness.",
        provider="coingecko_global",
        # Ambiguous sign for score_macro(): rising dominance is BTC-bullish
        # but alt-bearish, and the same FactorScore is used for every
        # watchlist symbol regardless of whether it's BTC or an alt — so
        # this stays a displayed-only indicator, same as Silver/Oil.
        used_in_scoring=False,
    ),
]

MACRO_INDICATOR_IDS: list[str] = [ind.id for ind in MACRO_INDICATORS]


def get_indicator_def(indicator_id: str) -> MacroIndicatorDef:
    for ind in MACRO_INDICATORS:
        if ind.id == indicator_id:
            return ind
    raise KeyError(f"Unknown macro indicator: {indicator_id}")
