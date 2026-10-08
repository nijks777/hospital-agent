from sqlmodel.ext.asyncio.session import AsyncSession

from hospital_agent.repositories.email_verification_repository import (
    EmailVerificationRepository,
)
from hospital_agent.repositories.hospital_repository import HospitalRepository
from hospital_agent.repositories.user_repository import UserRepository


class UnitOfWork:
    """All repositories for one request, sharing one DB transaction.

    Services change data through the repositories, then call `commit()` once.
    If anything fails before that, nothing is saved (the session rolls back on close).
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.hospitals = HospitalRepository(session)
        self.email_verifications = EmailVerificationRepository(session)

    async def commit(self) -> None:
        await self.session.commit()
