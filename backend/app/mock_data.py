"""Mock data generators for the endpoints that stay mock in Sprint 2
(AI signals, portfolio, news, whales, liquidations, macro, backtesting, chat).

Market data (assets, candles, funding, open interest, indicators) is now
served from the real Binance-backed Data Engine — see `app/services` and
`app/api/market.py`, `candles.py`, `indicators.py`, `funding.py`,
`open_interest.py`.
"""

import time
from datetime import UTC, datetime, timedelta

from app.schemas.backtest import BacktestResult, EquityPoint
from app.schemas.macro import MacroEvent, MacroIndicator
from app.schemas.news import NewsItem
from app.schemas.portfolio import PortfolioSummary, Position, TradeHistoryItem
from app.schemas.whale import WhaleTransaction


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
            opened_at=(datetime.now(UTC) - timedelta(hours=26)).isoformat(),
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
            opened_at=(datetime.now(UTC) - timedelta(hours=9)).isoformat(),
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
            opened_at=(datetime.now(UTC) - timedelta(hours=96)).isoformat(),
            closed_at=(datetime.now(UTC) - timedelta(hours=48)).isoformat(),
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
            published_at=(datetime.now(UTC) - timedelta(minutes=index * 47)).isoformat(),
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
                timestamp=(datetime.now(UTC) - timedelta(minutes=index * 14)).isoformat(),
                tx_hash=f"0x{(index * 928371 + 5555):010x}",
            )
        )
    return transactions


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
            date=(datetime.now(UTC) + timedelta(days=2)).isoformat(),
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
