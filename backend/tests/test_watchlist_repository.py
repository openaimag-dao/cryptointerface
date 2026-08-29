import pytest

from app.services.user_repository import create_user
from app.services.watchlist_repository import add_watchlist_symbol, list_watchlist_symbols, remove_watchlist_symbol


async def _make_user(db_session, email: str) -> int:
    user = await create_user(db_session, email=email, hashed_password="x", display_name=None)
    return user.id


@pytest.mark.asyncio
async def test_add_watchlist_symbol_returns_true_for_a_new_entry(db_session):
    user_id = await _make_user(db_session, "a@example.com")

    added = await add_watchlist_symbol(db_session, user_id=user_id, symbol="BTC")

    assert added is True
    assert await list_watchlist_symbols(db_session, user_id=user_id) == ["BTC"]


@pytest.mark.asyncio
async def test_add_watchlist_symbol_is_idempotent(db_session):
    user_id = await _make_user(db_session, "b@example.com")

    first = await add_watchlist_symbol(db_session, user_id=user_id, symbol="ETH")
    second = await add_watchlist_symbol(db_session, user_id=user_id, symbol="ETH")

    assert first is True
    assert second is False
    assert await list_watchlist_symbols(db_session, user_id=user_id) == ["ETH"]


@pytest.mark.asyncio
async def test_list_watchlist_symbols_scoped_per_user(db_session):
    user_1 = await _make_user(db_session, "c@example.com")
    user_2 = await _make_user(db_session, "d@example.com")
    await add_watchlist_symbol(db_session, user_id=user_1, symbol="BTC")
    await add_watchlist_symbol(db_session, user_id=user_2, symbol="SOL")

    assert await list_watchlist_symbols(db_session, user_id=user_1) == ["BTC"]
    assert await list_watchlist_symbols(db_session, user_id=user_2) == ["SOL"]


@pytest.mark.asyncio
async def test_remove_watchlist_symbol_removes_it(db_session):
    user_id = await _make_user(db_session, "e@example.com")
    await add_watchlist_symbol(db_session, user_id=user_id, symbol="BTC")

    removed = await remove_watchlist_symbol(db_session, user_id=user_id, symbol="BTC")

    assert removed is True
    assert await list_watchlist_symbols(db_session, user_id=user_id) == []


@pytest.mark.asyncio
async def test_remove_watchlist_symbol_returns_false_when_nothing_to_remove(db_session):
    user_id = await _make_user(db_session, "f@example.com")
    removed = await remove_watchlist_symbol(db_session, user_id=user_id, symbol="DOGE")
    assert removed is False
