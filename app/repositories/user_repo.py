from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.user_schema import UserCreate
from app.core.security import get_password_hash


class UserRepository:
    async def get_by_username(self, db: AsyncSession, username: str):
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, db: AsyncSession, user_id: int):
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, obj_in: UserCreate):
        hashed_password = get_password_hash(obj_in.password)
        db_obj = User(username=obj_in.username, password_hash=hashed_password)
        db.add(db_obj)
        await db.flush()  # Thay commit() bằng flush()
        await db.refresh(db_obj)
        return db_obj


user_repo = UserRepository()
