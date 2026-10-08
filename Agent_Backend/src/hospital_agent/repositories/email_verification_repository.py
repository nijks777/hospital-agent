import uuid

from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from hospital_agent.models.email_verification import EmailVerification


class EmailVerificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_latest_for_user(self, user_id: uuid.UUID) -> EmailVerification | None:
        result = await self.session.exec(
            select(EmailVerification)
            .where(EmailVerification.user_id == user_id)
            .order_by(col(EmailVerification.created_at).desc())
            .limit(1)
        )
        return result.first()

    async def add(self, verification: EmailVerification) -> EmailVerification:
        self.session.add(verification)
        await self.session.flush()
        return verification
