import pytest

from app.services.auth_service import hash_password
from app.services.user_repository import create_user, get_user_by_email, get_user_by_id


@pytest.mark.asyncio
async def test_create_user_and_get_by_email(db_session):
    created = await create_user(
        db_session, email="a@example.com", hashed_password=hash_password("password123"), display_name="Ada"
    )

    fetched = await get_user_by_email(db_session, "a@example.com")

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.display_name == "Ada"
    assert fetched.role == "user"
    assert fetched.is_active is True


@pytest.mark.asyncio
async def test_get_user_by_email_returns_none_for_unknown_email(db_session):
    assert await get_user_by_email(db_session, "nobody@example.com") is None


@pytest.mark.asyncio
async def test_get_user_by_id_returns_none_for_unknown_id(db_session):
    assert await get_user_by_id(db_session, 999999) is None


@pytest.mark.asyncio
async def test_get_user_by_id_returns_the_created_user(db_session):
    created = await create_user(
        db_session, email="b@example.com", hashed_password=hash_password("password123"), display_name=None
    )

    fetched = await get_user_by_id(db_session, created.id)

    assert fetched is not None
    assert fetched.email == "b@example.com"
