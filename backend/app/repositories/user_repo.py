from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

async def get_by_id(db: AsyncSession, user_id: UUID | str) -> User | None:
    if isinstance(user_id, str):
        from uuid import UUID as pyUUID
        user_id = pyUUID(user_id)
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()

async def get_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()

async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def create(db: AsyncSession, username: str, email: str, password_hash: str) -> User:
    db_user = User(username=username, email=email, password_hash=password_hash)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def list_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[User]:
    result = await db.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())

async def update(db: AsyncSession, user: User, **kwargs) -> User:
    for key, value in kwargs.items():
        setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user

async def delete(db: AsyncSession, user: User) -> None:
    await db.delete(user)
    await db.commit()
