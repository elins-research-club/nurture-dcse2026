import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.config import settings
from app.core.security import get_password_hash
from app.repositories import user_repo

async def init_admin():
    async with AsyncSessionLocal() as db:
        admin_email = settings.FIRST_SUPERUSER_EMAIL
        admin = await user_repo.get_by_email(db, admin_email)
        if not admin:
            print("Creating first superuser...")
            await user_repo.create(
                db=db,
                username="admin",
                email=admin_email,
                password_hash=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD)
            )
            print("Admin user created successfully!")

if __name__ == "__main__":
    asyncio.run(main())
