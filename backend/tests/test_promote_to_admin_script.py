import pytest

import scripts.promote_to_admin as promote_to_admin_module
from app.services.auth_service import hash_password
from app.services.user_repository import create_user, get_user_by_email
from scripts.promote_to_admin import promote


class _NoCloseSessionContext:
    """Wraps the shared `db_session` test fixture so `async with
    AsyncSessionLocal() as db:` in the script under test doesn't close the
    fixture's connection out from under later assertions in the same
    test."""

    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, *exc_info):
        return False


@pytest.fixture(autouse=True)
def _patch_session_factory(db_session, monkeypatch):
    monkeypatch.setattr(promote_to_admin_module, "AsyncSessionLocal", lambda: _NoCloseSessionContext(db_session))


@pytest.mark.asyncio
async def test_promote_sets_role_to_admin(db_session):
    await create_user(
        db_session, email="future-admin@example.com", hashed_password=hash_password("x"), display_name=None
    )

    result = await promote("future-admin@example.com")

    assert result is True
    user = await get_user_by_email(db_session, "future-admin@example.com")
    assert user.role == "admin"


@pytest.mark.asyncio
async def test_promote_returns_false_for_unknown_email(db_session):
    result = await promote("nobody@example.com")

    assert result is False
