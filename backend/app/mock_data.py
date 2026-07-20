"""Mock data generators.

Sprint 2 will replace these with real Binance market data calls and the AI
reasoning engine. Endpoints in `app/routers` should keep the same response
shapes so the frontend requires no changes when live data is wired in.
"""

import random
import time
from datetime import datetime, timedelta, timezone

from app.models.backtest import BacktestResult, EquityPoint
from app.models.liquidation import LiquidationEvent, LiquidationHeatmapCell
from app.models.macro import MacroEvent, MacroIndicator
from app.models.market import AssetQuote, Candle, MarketOverview
from app.models.news import NewsItem
from app.models.portfolio import PortfolioSummary, Position, TradeHistoryItem
from app.models.signal import AiAnalysis, AiSignal
from app.models.whale import WhaleTransaction

ASSET_SEEDS = [
    {"symbol": "BTCUSDT", "name": "Bitcoin", "price": 64280.5, "ai_score": 76, "direction": "LONG"},
    {"symbol": "ETHUSDT", "name": "Ethereum", "price": 3412.8, "ai_score": 54, "direction": "WAIT"},
    {"symbol": "SOLUSDT", "name": "Solana", "price": 172.34, "ai_score": 88, "direction": "LONG"},
    {"symbol": "LINKUSDT", "name": "Chainlink", "price": 18.62, "ai_score": 29, "direction": "SHORT"},
    {"symbol": "BNBUSDT", "name": "BNB", "price": 592.1, "ai_score": 41, "direction": "WAIT"},
    {"symbol": "XRPUSDT", "name": "XRP", "price": 0.612, "ai_score": 39, "direction": "WAIT"},
    {"symbol": "AVAXUSDT", "name": "Avalanche", "price": 38.47, "ai_score": 62, "direction": "WAIT"},
    {"symbol": "DOGEUSDT", "name": "Dogecoin", "price": 0.1523, "ai_score": 30, "direction": "SHORT"},
    {"symbol": "ADAUSDT", "name": "Cardano", "price": 0.478, "ai_score": 56, "direction": "WAIT"},
    {"symbol": "TONUSDT", "name": "Toncoin", "price": 6.94, "ai_score": 82, "direction": "LONG"},
]

WATCHLIST_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "LINKUSDT"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_assets() -> list[AssetQuote]:
    assets = []
    for seed in ASSET_SEEDS:
        seed_hash = sum(ord(char) for char in seed["symbol"])
        assets.append(
            AssetQuote(
                symbol=seed["symbol"],
                name=seed["name"],
                price=seed["price"],
                change_percent_24h=round(((seed_hash % 900) - 450) / 40, 2),
                volume_24h=80_000_000 + (seed_hash % 40) * 32_000_000,
                funding_rate=round(((seed_hash % 40) - 20) / 1000, 5),
                open_interest=200_000_000 + (seed_hash % 50) * 18_000_000,
                ai_score=seed["ai_score"],
                direction=seed["direction"],
            )
        )
    return assets


def get_asset(symbol: str) -> AssetQuote | None:
    return next((asset for asset in get_assets() if asset.symbol == symbol), None)


def get_market_overview() -> MarketOverview:
    return MarketOverview(
        fear_greed_index=62,
        fear_greed_label="Greed",
        btc_dominance=54.2,
        avg_funding_rate=0.0086,
        total_open_interest=38_400_000_000,
        total_volume_24h=96_200_000_000,
    )


def get_candles(symbol: str, base_price: float, count: int = 180) -> list[Candle]:
    rng = random.Random(sum(ord(char) for char in symbol))
    candles: list[Candle] = []
    price = base_price
    now = int(time.time())
    interval_seconds = 3600

    for i in range(count, -1, -1):
        candle_time = now - i * interval_seconds
        volatility = base_price * 0.006
        drift = (rng.random() - 0.48) * volatility
        open_price = price
        close_price = max(open_price + drift, base_price * 0.5)
        high_price = max(open_price, close_price) + rng.random() * volatility * 0.6
        low_price = min(open_price, close_price) - rng.random() * volatility * 0.6
        volume = 1200 + rng.random() * 4200

        candles.append(
            Candle(
                time=candle_time,
                open=round(open_price, 2),
                high=round(high_price, 2),
                low=round(low_price, 2),
                close=round(close_price, 2),
                volume=round(volume, 2),
            )
        )
        price = close_price

    return candles


_SIGNAL_SEEDS = [
    {"symbol": "SOLUSDT", "direction": "LONG", "entry": 172.4, "confidence": 88},
    {"symbol": "BTCUSDT", "direction": "LONG", "entry": 64280, "confidence": 76},
    {"symbol": "ETHUSDT", "direction": "WAIT", "entry": 3412, "confidence": 54},
    {"symbol": "LINKUSDT", "direction": "SHORT", "entry": 18.62, "confidence": 71},
    {"symbol": "AVAXUSDT", "direction": "LONG", "entry": 38.4, "confidence": 82},
    {"symbol": "DOGEUSDT", "direction": "SHORT", "entry": 0.1523, "confidence": 66},
]

_REASON_POOL = {
    "LONG": [
        "Price reclaimed the daily VWAP with rising volume",
        "RSI bullish divergence confirmed on the 4H chart",
        "Funding rate reset to neutral after long liquidations",
    ],
    "SHORT": [
        "Rejection at key resistance with bearish engulfing candle",
        "Funding rate overheated, crowded long positioning",
        "Open interest spiking without price confirmation",
    ],
    "WAIT": [
        "Price is consolidating inside a tight range",
        "Conflicting signals between momentum and volume",
        "Awaiting confirmation candle beyond range boundaries",
    ],
}


def get_signals() -> list[AiSignal]:
    signals = []
    for index, seed in enumerate(_SIGNAL_SEEDS):
        risk_unit = seed["entry"] * 0.018
        direction = seed["direction"]
        stop_loss = seed["entry"] + risk_unit if direction == "SHORT" else seed["entry"] - risk_unit
        tp_multiplier = -1 if direction == "SHORT" else 1

        signals.append(
            AiSignal(
                id=f"sig-{index}-{seed['symbol']}",
                symbol=seed["symbol"],
                direction=direction,
                confidence=seed["confidence"],
                entry=seed["entry"],
                stop_loss=round(stop_loss, 4),
                take_profit_1=round(seed["entry"] + tp_multiplier * risk_unit * 1.5, 4),
                take_profit_2=round(seed["entry"] + tp_multiplier * risk_unit * 2.5, 4),
                take_profit_3=round(seed["entry"] + tp_multiplier * risk_unit * 4, 4),
                risk_reward=round(2 + (index % 3), 1),
                reasons=_REASON_POOL[direction][:3],
                created_at=(datetime.now(timezone.utc) - timedelta(minutes=index * 37)).isoformat(),
                timeframe=["15m", "1H", "4H"][index % 3],
            )
        )
    return signals


def get_ai_analysis(symbol: str) -> AiAnalysis:
    signal = next((s for s in get_signals() if s.symbol == symbol), None)
    direction = signal.direction if signal else "LONG"
    entry = signal.entry if signal else 64280
    risk_unit = entry * 0.018

    return AiAnalysis(
        symbol=symbol,
        ai_score=signal.confidence if signal else 70,
        direction=direction,
        confidence=signal.confidence if signal else 70,
        reasons=signal.reasons if signal else _REASON_POOL[direction][:3],
        entry=entry,
        stop_loss=signal.stop_loss if signal else entry - risk_unit,
        take_profit_1=signal.take_profit_1 if signal else entry + risk_unit * 1.5,
        take_profit_2=signal.take_profit_2 if signal else entry + risk_unit * 2.5,
        take_profit_3=signal.take_profit_3 if signal else entry + risk_unit * 4,
        risk=round(risk_unit, 4),
        reward=round(risk_unit * 2.5, 4),
    )


def get_portfolio() -> PortfolioSummary:
    open_positions = [
        Position(
            id="pos-1",
            symbol="BTCUSDT",
            direction="LONG",
            size=0.42,
            entry_price=61200,
            mark_price=64280.5,
            pnl=1293.8,
            pnl_percent=5.03,
            leverage=5,
            opened_at=(datetime.now(timezone.utc) - timedelta(hours=26)).isoformat(),
        ),
        Position(
            id="pos-2",
            symbol="SOLUSDT",
            direction="LONG",
            size=65,
            entry_price=158.2,
            mark_price=172.34,
            pnl=918.1,
            pnl_percent=8.94,
            leverage=3,
            opened_at=(datetime.now(timezone.utc) - timedelta(hours=9)).isoformat(),
        ),
    ]
    history = [
        TradeHistoryItem(
            id="trade-1",
            symbol="ETHUSDT",
            direction="LONG",
            entry_price=3180,
            exit_price=3412.8,
            pnl=698.4,
            pnl_percent=7.32,
            opened_at=(datetime.now(timezone.utc) - timedelta(hours=96)).isoformat(),
            closed_at=(datetime.now(timezone.utc) - timedelta(hours=48)).isoformat(),
        ),
    ]
    total_pnl = sum(position.pnl for position in open_positions)
    balance = 42_500.0

    return PortfolioSummary(
        balance=balance,
        equity=balance + total_pnl,
        total_pnl=total_pnl,
        total_pnl_percent=round((total_pnl / balance) * 100, 2),
        win_rate=68.4,
        total_trades=156,
        open_positions=open_positions,
        history=history,
    )


def get_news() -> list[NewsItem]:
    seeds = [
        {
            "title": "Bitcoin ETF inflows hit $620M as institutional demand accelerates",
            "summary": "Spot Bitcoin ETFs recorded their largest single-day inflow in three months.",
            "source": "Bloomberg Crypto",
            "sentiment": "BULLISH",
            "tags": ["BTC", "ETF", "Institutional"],
        },
        {
            "title": "Regulators signal tighter scrutiny on stablecoin reserves",
            "summary": "A new proposal could require weekly attestations for large issuers.",
            "source": "Reuters",
            "sentiment": "BEARISH",
            "tags": ["Regulation", "Stablecoins"],
        },
    ]
    return [
        NewsItem(
            id=f"news-{index}",
            title=seed["title"],
            summary=seed["summary"],
            source=seed["source"],
            published_at=(datetime.now(timezone.utc) - timedelta(minutes=index * 47)).isoformat(),
            sentiment=seed["sentiment"],
            tags=seed["tags"],
            url="#",
        )
        for index, seed in enumerate(seeds)
    ]


def get_whale_transactions(count: int = 24) -> list[WhaleTransaction]:
    types = ["TRANSFER", "DEPOSIT", "WITHDRAWAL", "SWAP"]
    symbols = ["BTC", "ETH", "SOL", "USDT", "LINK"]
    exchanges = ["Binance", "Coinbase", "OKX", "Bybit", None]

    transactions = []
    for index in range(count):
        symbol = symbols[index % len(symbols)]
        amount = 50 + (index * 137) % 900
        price = {"BTC": 64280, "ETH": 3412, "SOL": 172, "USDT": 1, "LINK": 18.6}[symbol]
        transactions.append(
            WhaleTransaction(
                id=f"whale-{index}",
                symbol=symbol,
                type=types[index % len(types)],
                amount=amount,
                amount_usd=round(amount * price * (10 if symbol == "BTC" else 1)),
                from_address=f"0x{(index * 291 + 173) % 999999:06x}",
                to_address=f"0x{(index * 71) % 999999:06x}",
                exchange=exchanges[index % len(exchanges)],
                timestamp=(datetime.now(timezone.utc) - timedelta(minutes=index * 14)).isoformat(),
                tx_hash=f"0x{(index * 928371 + 5555):010x}",
            )
        )
    return transactions


def get_liquidations(count: int = 30) -> list[LiquidationEvent]:
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "LINKUSDT", "AVAXUSDT"]
    exchanges = ["Binance", "OKX", "Bybit", "Bitget"]
    base_prices = {"BTCUSDT": 64280, "ETHUSDT": 3412, "SOLUSDT": 172, "LINKUSDT": 18.6, "AVAXUSDT": 38.4}

    events = []
    for index in range(count):
        symbol = symbols[index % len(symbols)]
        side = "SHORT" if index % 3 == 0 else "LONG"
        events.append(
            LiquidationEvent(
                id=f"liq-{index}",
                symbol=symbol,
                side=side,
                amount_usd=8_000 + (index * 2917) % 480_000,
                price=round(base_prices[symbol] * (1 + ((index % 7) - 3) / 500), 2),
                exchange=exchanges[index % len(exchanges)],
                timestamp=(datetime.now(timezone.utc) - timedelta(minutes=index * 6)).isoformat(),
            )
        )
    return events


def get_liquidation_heatmap(base_price: float = 64280, count: int = 40) -> list[LiquidationHeatmapCell]:
    import math

    cells = []
    for index in range(count):
        offset = (index - count / 2) * (base_price * 0.0025)
        distance_factor = abs(index - count / 2) / (count / 2)
        cells.append(
            LiquidationHeatmapCell(
                price=round(base_price + offset, 2),
                intensity=round(max(0.08, 1 - distance_factor + math.sin(index) * 0.15), 2),
            )
        )
    return cells


def get_macro_indicators() -> list[MacroIndicator]:
    return [
        MacroIndicator(
            id="dxy",
            label="DXY Dollar Index",
            value="104.32",
            change_label="-0.18%",
            sentiment="POSITIVE",
            description="Weaker dollar historically correlates with crypto strength.",
        ),
        MacroIndicator(
            id="us10y",
            label="US 10Y Yield",
            value="4.28%",
            change_label="+0.04",
            sentiment="NEGATIVE",
            description="Rising yields increase opportunity cost of holding risk assets.",
        ),
    ]


def get_macro_events() -> list[MacroEvent]:
    return [
        MacroEvent(
            id="evt-1",
            title="FOMC Interest Rate Decision",
            date=(datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
            impact="HIGH",
            forecast="5.25% - 5.50%",
            previous="5.25% - 5.50%",
        ),
    ]


def get_backtest_result(strategy: str, symbol: str, timeframe: str) -> BacktestResult:
    points = 60
    equity = 10_000.0
    day_seconds = 60 * 60 * 24
    start_time = int(time.time()) - points * day_seconds
    curve = []

    import math

    for index in range(points):
        equity *= 1 + (math.sin(index / 4) * 0.006 + 0.0045)
        curve.append(EquityPoint(time=start_time + index * day_seconds, value=round(equity, 2)))

    return BacktestResult(
        id=f"bt-{strategy}-{symbol}-{timeframe}",
        strategy=strategy,
        symbol=symbol,
        timeframe=timeframe,
        period="Jan 2025 - Jul 2026",
        total_trades=214,
        win_rate=61.3,
        profit_factor=1.84,
        total_return_percent=round(((equity - 10_000) / 10_000) * 100, 1),
        max_drawdown_percent=-14.2,
        sharpe_ratio=1.62,
        equity_curve=curve,
    )


CHAT_STUB_RESPONSES = [
    "This is a placeholder response. In Sprint 2, this will be powered by the AIMAG AI reasoning engine connected to live Binance data.",
    "I don't have live market access yet, once the AI module is connected I'll analyze this in real time.",
]


def get_chat_stub_response() -> str:
    return random.choice(CHAT_STUB_RESPONSES)
