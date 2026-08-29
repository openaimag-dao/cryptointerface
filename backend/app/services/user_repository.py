from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def create_user(db: AsyncSession, *, email: str, hashed_password: str, display_name: str | None) -> User:
    user = User(email=email, hashed_password=hashed_password, display_name=display_name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    return await db.get(User, user_id)
