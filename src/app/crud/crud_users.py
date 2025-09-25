from fastcrud import FastCRUD
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from ..schemas.user import UserCreateInternal, UserDelete, UserUpdate, UserUpdateInternal

class CRUDUser(FastCRUD[User, UserCreateInternal, UserUpdate, UserUpdateInternal, UserDelete, None]):
    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        """Get a user by email"""
        query = select(self.model).where(self.model.email == email)
        result = await db.execute(query)
        return result.scalar_one_or_none()

crud_users = CRUDUser(User)
