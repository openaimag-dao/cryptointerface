"""Registry of every macro indicator the Macro Engine tracks.

To add a new indicator: add one entry here, then handle its `provider`
value in `providers.py`/`service.py` if it isn't one of the existing three
providers. Nothing else needs to change — `/api/macro/indicators` and the
scheduler both iterate this registry.

Free-tier reality check: none of DXY/Gold/Silver/Oil/NASDAQ/S&P 500/VIX
have a direct free index feed, so these are tracked via liquid, highly
correlated ETF proxies through Alpha Vantage's `TIME_SERIES_DAILY` (a
single generic endpoint) — e.g. `UUP` for the Dollar Index, `GLD` for
Gold spot. US 10Y uses Alpha Vantage's dedicated `TREASURY_YIELD`
endpoint instead (a real yield, not a proxy). Fear & Greed and BTC
Dominance are free/keyless (`alternative.me`, CoinGecko `/global`).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MacroIndicatorDef:
    id: str
    label: str
    description: str
    provider: str  # "alpha_vantage_etf" | "alpha_vantage_treasury" | "fear_greed" | "coingecko_global"
    # Alpha Vantage ETF ticker (only set when provider == "alpha_vantage_etf")
    av_ticker: str | None = None
    # Whether score_macro() (app/ai_engine/scoring/macro.py) uses this
    # indicator. A few (Silver, Oil) are tracked/displayed but have too
    # weak/ambiguous a direct correlation to crypto risk sentiment to be
    # worth a scoring sub-weight — see that module's docstring.
    used_in_scoring: bool = True


MACRO_INDICATORS: list[MacroIndicatorDef] = [
    MacroIndicatorDef(
        id="dxy",
        label="DXY Dollar Index (UUP proxy)",
        description="Weaker dollar historically correlates with crypto strength.",
        provider="alpha_vantage_etf",
        av_ticker="UUP",
    ),
    MacroIndicatorDef(
        id="gold",
        label="Gold Spot (GLD proxy)",
        description="Safe-haven demand alongside BTC's 'digital gold' narrative.",
        provider="alpha_vantage_etf",
        av_ticker="GLD",
    ),
    MacroIndicatorDef(
        id="silver",
        label="Silver Spot (SLV proxy)",
        description="Industrial + precious-metal demand; tracked for context, not scored.",
        provider="alpha_vantage_etf",
        av_ticker="SLV",
        used_in_scoring=False,
    ),
    MacroIndicatorDef(
        id="oil",
        label="Crude Oil - WTI (USO proxy)",
        description="Broad inflation/risk-appetite proxy; tracked for context, not scored.",
        provider="alpha_vantage_etf",
        av_ticker="USO",
        used_in_scoring=False,
    ),
    MacroIndicatorDef(
        id="sp500",
        label="S&P 500 (SPY proxy)",
        description="Risk-on equities strength tends to correlate with crypto strength.",
        provider="alpha_vantage_etf",
        av_ticker="SPY",
    ),
    MacroIndicatorDef(
        id="nasdaq",
        label="NASDAQ 100 (QQQ proxy)",
        description="Tech-heavy risk appetite, the most crypto-correlated equity index.",
        provider="alpha_vantage_etf",
        av_ticker="QQQ",
    ),
    MacroIndicatorDef(
        id="vix",
        label="VIX Volatility (VIXY proxy)",
        description="Elevated equity fear historically coincides with crypto de-risking.",
        provider="alpha_vantage_etf",
        av_ticker="VIXY",
    ),
    MacroIndicatorDef(
        id="us10y",
        label="US 10Y Yield",
        description="Rising yields raise the opportunity cost of holding non-yielding risk assets.",
        provider="alpha_vantage_treasury",
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
