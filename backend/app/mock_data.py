"""Mock data generators for the endpoints that stay mock
(portfolio, whales, macro events, backtesting).

Market data (assets, candles, funding, open interest, indicators) is
served from the real Binance-backed Data Engine — see `app/services` and
`app/api/market.py`, `candles.py`, `indicators.py`, `funding.py`,
`open_interest.py`. News, signals, liquidations, and chat are also real
now — see `app/intelligence/`, `app/api/signals.py`, `liquidations.py`,
`chat.py`.
"""

import time
from datetime import UTC, datetime, timedelta

from app.schemas.backtest import BacktestResult, EquityPoint
from app.schemas.macro import MacroEvent
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
