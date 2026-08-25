import asyncio

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.repositories import user_repo

ADMIN_USERNAME = "gconnect"
ADMIN_EMAIL = "gconnect@elins.ugm.ac.id"
ADMIN_PASSWORD = "atminelins123"


async def init_admin():
    async with AsyncSessionLocal() as db:
        if await user_repo.get_by_email(db, ADMIN_EMAIL):
            print(f"User {ADMIN_EMAIL} sudah ada, dilewati.")
            return

        await user_repo.create(
            db=db,
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
        )
        print(f"User '{ADMIN_USERNAME}' berhasil dibuat.")


if __name__ == "__main__":
    asyncio.run(init_admin())
