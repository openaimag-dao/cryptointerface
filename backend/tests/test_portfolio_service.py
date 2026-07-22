import pytest

from app.core.config import get_settings
from app.services import portfolio_service as portfolio_service_module
from app.services.binance.account_client import AccountBalance, PositionRisk, UserTrade
from app.services.portfolio_service import (
    _closing_trade_to_history_item,
    _to_position,
    get_real_portfolio,
)

settings = get_settings()


def test_to_position_long_from_positive_amount():
    risk = PositionRisk(
        symbol="BTCUSDT",
        position_amt=0.5,
        entry_price=60000.0,
        mark_price=62000.0,
        unrealized_profit=1000.0,
        leverage=10,
        update_time=1_700_000_000_000,
    )

    position = _to_position(risk)

    assert position.direction == "LONG"
    assert position.size == 0.5
    assert position.pnl == 1000.0
    assert position.pnl_percent == pytest.approx(round(1000.0 / (0.5 * 60000.0) * 100.0, 2))


def test_to_position_short_from_negative_amount():
    risk = PositionRisk(
        symbol="ETHUSDT",
        position_amt=-2.0,
        entry_price=3000.0,
        mark_price=2900.0,
        unrealized_profit=200.0,
        leverage=5,
        update_time=1_700_000_000_000,
    )

    position = _to_position(risk)

    assert position.direction == "SHORT"
    assert position.size == 2.0


def test_closing_trade_sell_fill_derives_long_close_and_entry_price():
    # A SELL fill that realized profit closed a LONG. exit=3500, pnl=300,
    # qty=1 -> entry = exit - pnl/qty = 3200.
    trade = UserTrade(
        symbol="ETHUSDT", id=1, side="SELL", price=3500.0, qty=1.0, realized_pnl=300.0, time=1_700_000_000_000
    )

    item = _closing_trade_to_history_item(trade)

    assert item is not None
    assert item.direction == "LONG"
    assert item.exit_price == 3500.0
    assert item.entry_price == pytest.approx(3200.0)
    assert item.pnl == 300.0


def test_closing_trade_buy_fill_derives_short_close_and_entry_price():
    # A BUY fill that realized profit closed a SHORT. exit=3000, pnl=400,
    # qty=2 -> entry = exit + pnl/qty = 3200.
    trade = UserTrade(
        symbol="ETHUSDT", id=2, side="BUY", price=3000.0, qty=2.0, realized_pnl=400.0, time=1_700_000_000_000
    )

    item = _closing_trade_to_history_item(trade)

    assert item is not None
    assert item.direction == "SHORT"
    assert item.exit_price == 3000.0
    assert item.entry_price == pytest.approx(3200.0)


def test_closing_trade_zero_qty_returns_none():
    trade = UserTrade(
        symbol="ETHUSDT", id=3, side="SELL", price=3000.0, qty=0.0, realized_pnl=0.0, time=1_700_000_000_000
    )

    assert _closing_trade_to_history_item(trade) is None


@pytest.mark.asyncio
async def test_get_real_portfolio_returns_none_without_api_key(monkeypatch):
    monkeypatch.setattr(settings, "binance_api_key", "")
    monkeypatch.setattr(settings, "binance_api_secret", "")

    result = await get_real_portfolio()

    assert result is None


@pytest.mark.asyncio
async def test_get_real_portfolio_returns_none_on_client_error(monkeypatch):
    monkeypatch.setattr(settings, "binance_api_key", "test-key")
    monkeypatch.setattr(settings, "binance_api_secret", "test-secret")

    class _RaisingClient:
        async def __aenter__(self):
            raise ConnectionError("unreachable")

        async def __aexit__(self, *exc_info):
            return False

    monkeypatch.setattr(portfolio_service_module, "BinanceAccountClient", lambda: _RaisingClient())

    result = await get_real_portfolio()

    assert result is None


@pytest.mark.asyncio
async def test_get_real_portfolio_builds_summary_from_real_account_data(monkeypatch):
    monkeypatch.setattr(settings, "binance_api_key", "test-key")
    monkeypatch.setattr(settings, "binance_api_secret", "test-secret")
    monkeypatch.setattr(settings, "symbols", "BTCUSDT")

    class _FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc_info):
            return False

        async def get_balances(self):
            return [
                AccountBalance(
                    asset="USDT",
                    balance=10000.0,
                    cross_wallet_balance=10000.0,
                    cross_unrealized_pnl=0.0,
                    available_balance=9000.0,
                )
            ]

        async def get_position_risk(self):
            return [
                PositionRisk(
                    symbol="BTCUSDT",
                    position_amt=0.1,
                    entry_price=60000.0,
                    mark_price=61000.0,
                    unrealized_profit=100.0,
                    leverage=5,
                    update_time=1_700_000_000_000,
                )
            ]

        async def get_user_trades(self, symbol, limit=20):
            return [
                UserTrade(
                    symbol=symbol, id=1, side="SELL", price=59000.0, qty=0.2, realized_pnl=200.0, time=1_700_000_000_000
                )
            ]

    monkeypatch.setattr(portfolio_service_module, "BinanceAccountClient", lambda: _FakeClient())

    result = await get_real_portfolio()

    assert result is not None
    assert result.balance == 10000.0
    assert len(result.open_positions) == 1
    assert result.open_positions[0].symbol == "BTCUSDT"
    assert result.total_trades == 1
    assert result.history[0].pnl == 200.0
    assert result.win_rate == 100.0
