import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password

async def main():
    async with AsyncSessionLocal() as db:
        user = User(
            username="admin",
            email="admin@elins.ugm.ac.id",
            password_hash=hash_password("atminelins123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(user)
        await db.commit()
        print("Admin user created successfully!")

if __name__ == "__main__":
    asyncio.run(main())
