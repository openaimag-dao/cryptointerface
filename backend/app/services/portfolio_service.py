"""Portfolio — real Binance USDT-M Futures account data (wallet balance,
open positions, realized-PnL trade history) for the single service account
configured via `BINANCE_API_KEY`/`BINANCE_API_SECRET` (see .env.example).

This app has no user/auth system, so there is exactly one portfolio: the
account those credentials belong to — the same "one shared account, not
multi-tenant" scope every other API-keyed integration in this app uses
(Etherscan, Alpha Vantage, Anthropic). Degrades to `None` — never raises —
when no key is configured or the account API is unreachable, so the caller
(`app/api/portfolio.py`) can fall back to `mock_data.get_portfolio()`, the
same fail-open discipline `app/tasks/coingecko_fallback.py` uses when
Binance's public market-data API is unreachable.

Trade history is derived, not fabricated: Binance's realized-PnL fills
(`userTrades` where `realizedPnl != 0`) give an exact closing price and
PnL, but not the paired entry fill's price. In one-way position mode a
closing fill's `side` alone determines direction (you can only close a
LONG by selling, a SHORT by buying), and the entry price follows exactly
from the PnL formula (`pnl = (exit - entry) * qty` for a LONG close,
`pnl = (entry - exit) * qty` for a SHORT close) — both are real,
back-derived numbers, not approximations.
"""

from datetime import UTC, datetime

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.portfolio import PortfolioSummary, Position, TradeHistoryItem
from app.services.binance.account_client import BinanceAccountClient, PositionRisk, UserTrade

logger = get_logger(__name__)
settings = get_settings()

TRADE_HISTORY_LIMIT_PER_SYMBOL = 20


def _iso(time_ms: int) -> str:
    return datetime.fromtimestamp(time_ms / 1000, tz=UTC).isoformat()


def _position_direction(position_amt: float) -> str:
    return "LONG" if position_amt >= 0 else "SHORT"


def _to_position(risk: PositionRisk) -> Position:
    notional = abs(risk.position_amt) * risk.entry_price
    pnl_percent = (risk.unrealized_profit / notional * 100.0) if notional > 0 else 0.0
    return Position(
        id=f"{risk.symbol}-{risk.update_time}",
        symbol=risk.symbol,
        direction=_position_direction(risk.position_amt),
        size=abs(risk.position_amt),
        entry_price=risk.entry_price,
        mark_price=risk.mark_price,
        pnl=risk.unrealized_profit,
        pnl_percent=round(pnl_percent, 2),
        leverage=risk.leverage,
        opened_at=_iso(risk.update_time),
    )


def _closing_trade_to_history_item(trade: UserTrade) -> TradeHistoryItem | None:
    """`trade` must be a closing/reducing fill (`realized_pnl != 0`).
    Returns None if the qty is zero (can't back out an entry price)."""
    if trade.qty <= 0:
        return None

    exit_price = trade.price
    # A SELL fill with non-zero realized PnL closed a LONG; a BUY fill
    # with non-zero realized PnL closed a SHORT (one-way position mode —
    # this is the only way to realize PnL on either side of a fill).
    if trade.side == "SELL":
        direction = "LONG"
        entry_price = exit_price - trade.realized_pnl / trade.qty
    else:
        direction = "SHORT"
        entry_price = exit_price + trade.realized_pnl / trade.qty

    notional = entry_price * trade.qty
    pnl_percent = (trade.realized_pnl / notional * 100.0) if notional > 0 else 0.0

    return TradeHistoryItem(
        id=str(trade.id),
        symbol=trade.symbol,
        direction=direction,
        entry_price=round(entry_price, 8),
        exit_price=round(exit_price, 8),
        pnl=round(trade.realized_pnl, 8),
        pnl_percent=round(pnl_percent, 2),
        opened_at=_iso(trade.time),  # the paired entry fill's real time isn't available; closing time stands in
        closed_at=_iso(trade.time),
    )


async def get_real_portfolio() -> PortfolioSummary | None:
    """`None` (never an exception) when no account is configured or it's
    unreachable — `app/api/portfolio.py` falls back to mock data then."""
    if not settings.binance_api_key or not settings.binance_api_secret:
        return None

    try:
        async with BinanceAccountClient() as client:
            balances = await client.get_balances()
            positions = await client.get_position_risk()
            trades_per_symbol = [
                await client.get_user_trades(symbol, limit=TRADE_HISTORY_LIMIT_PER_SYMBOL)
                for symbol in settings.symbol_list
            ]
    except Exception as exc:  # noqa: BLE001 — fail-open to mock, this must never 500 the endpoint
        logger.warning("binance_portfolio_fetch_failed", extra={"error": str(exc)})
        return None

    usdt_balance = next((b for b in balances if b.asset == "USDT"), None)
    if usdt_balance is None:
        return None

    open_positions = [_to_position(p) for p in positions if p.position_amt != 0]
    unrealized_total = sum(p.pnl for p in open_positions)

    closing_trades = [t for trades in trades_per_symbol for t in trades if t.realized_pnl != 0]
    closing_trades.sort(key=lambda t: t.time, reverse=True)
    history_items = [item for t in closing_trades if (item := _closing_trade_to_history_item(t)) is not None]

    realized_total = sum(item.pnl for item in history_items)
    wins = sum(1 for item in history_items if item.pnl > 0)
    win_rate = (wins / len(history_items) * 100.0) if history_items else 0.0

    balance = usdt_balance.balance
    equity = balance + unrealized_total
    total_pnl = unrealized_total + realized_total
    total_pnl_percent = (total_pnl / balance * 100.0) if balance > 0 else 0.0

    return PortfolioSummary(
        balance=round(balance, 2),
        equity=round(equity, 2),
        total_pnl=round(total_pnl, 2),
        total_pnl_percent=round(total_pnl_percent, 2),
        win_rate=round(win_rate, 1),
        total_trades=len(history_items),
        open_positions=open_positions,
        history=history_items,
    )
