import uuid

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from hospital_agent.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.exec(select(User).where(User.username == username))
        return result.first()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.exec(select(User).where(User.email == email))
        return result.first()

    async def add(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user
