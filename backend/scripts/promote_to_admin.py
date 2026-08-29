"""One-off script to promote a registered user to role="admin".

There is no in-app way to self-promote — that's a real security boundary,
not an oversight (see app/api/deps.py::get_current_admin_user). Run once
per new admin, from backend/:

    .venv/bin/python -m scripts.promote_to_admin someone@example.com
"""

import asyncio
import sys

from app.database.session import AsyncSessionLocal
from app.services.user_repository import get_user_by_email


async def promote(email: str) -> bool:
    async with AsyncSessionLocal() as db:
        user = await get_user_by_email(db, email)
        if user is None:
            return False
        user.role = "admin"
        await db.commit()
        return True


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.promote_to_admin <email>")
        sys.exit(1)

    email = sys.argv[1]
    promoted = asyncio.run(promote(email))
    if promoted:
        print(f"{email} is now an admin.")
    else:
        print(f"No user with email {email!r} — they must register first.")
        sys.exit(1)


if __name__ == "__main__":
    main()
