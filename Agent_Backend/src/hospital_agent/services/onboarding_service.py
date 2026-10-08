from datetime import timedelta

from sqlalchemy.exc import IntegrityError

from hospital_agent.core.config import Settings
from hospital_agent.core.security import (
    generate_verification_code,
    hash_password,
    hash_verification_code,
    verification_code_matches,
)
from hospital_agent.db.unit_of_work import UnitOfWork
from hospital_agent.integrations.email.port import EmailMessage, EmailSender
from hospital_agent.models.base import utcnow
from hospital_agent.models.email_verification import EmailVerification
from hospital_agent.models.hospital import Hospital, HospitalStatus
from hospital_agent.models.user import User, UserRole
from hospital_agent.schemas.onboarding import RegisterHospitalRequest


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCodeError(Exception):
    pass


class CodeExpiredError(Exception):
    pass


class TooManyAttemptsError(Exception):
    pass


class ResendTooSoonError(Exception):
    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__(retry_after_seconds)
        self.retry_after_seconds = retry_after_seconds


class OnboardingService:
    """Hospital registration and email verification."""

    def __init__(self, uow: UnitOfWork, email: EmailSender, settings: Settings) -> None:
        self.uow = uow
        self.email = email
        self.settings = settings

    async def register(self, data: RegisterHospitalRequest) -> Hospital:
        email = data.email.lower()
        if await self.uow.users.get_by_email(email) or await self.uow.users.get_by_username(email):
            raise EmailAlreadyRegisteredError

        hospital = await self.uow.hospitals.add(
            Hospital(
                name=data.hospital_name,
                city=data.city,
                contact_name=data.contact_name,
                contact_phone=data.phone,
                status=HospitalStatus.PENDING_VERIFICATION,
            )
        )
        user = await self.uow.users.add(
            User(
                username=email,
                email=email,
                password_hash=hash_password(data.password),
                role=UserRole.HOSPITAL_ADMIN,
                hospital_id=hospital.id,
            )
        )
        await self._send_new_code(user, hospital.name)
        # Commit only after the email went out: if sending fails, nothing is saved and the
        # applicant can simply submit the form again.
        try:
            await self.uow.commit()
        except IntegrityError:  # same email registered concurrently
            raise EmailAlreadyRegisteredError from None
        return hospital

    async def verify_email(self, email: str, code: str) -> None:
        user = await self.uow.users.get_by_email(email.lower())
        if user is None or user.role != UserRole.HOSPITAL_ADMIN:
            raise InvalidCodeError
        if user.email_verified_at is not None:
            return  # already verified: verifying twice is harmless

        verification = await self.uow.email_verifications.get_latest_for_user(user.id)
        now = utcnow()
        if verification is None or verification.consumed_at or verification.expires_at < now:
            raise CodeExpiredError
        if verification.attempts >= self.settings.verification_max_attempts:
            raise TooManyAttemptsError
        if not verification_code_matches(code, verification.code_hash, self.settings):
            verification.attempts += 1
            await self.uow.commit()
            raise InvalidCodeError

        hospital = await self.uow.hospitals.get_by_id(user.hospital_id)
        if hospital is None:
            raise InvalidCodeError
        verification.consumed_at = now
        user.email_verified_at = now
        hospital.transition_to(HospitalStatus.PENDING_REVIEW)
        await self.uow.commit()

    async def resend_code(self, email: str) -> None:
        """Silently does nothing for unknown or already-verified emails (no account probing)."""
        user = await self.uow.users.get_by_email(email.lower())
        if user is None or user.role != UserRole.HOSPITAL_ADMIN or user.email_verified_at:
            return

        latest = await self.uow.email_verifications.get_latest_for_user(user.id)
        if latest is not None:
            elapsed = (utcnow() - latest.created_at).total_seconds()
            cooldown = self.settings.verification_resend_cooldown_seconds
            if elapsed < cooldown:
                raise ResendTooSoonError(int(cooldown - elapsed) + 1)

        hospital = await self.uow.hospitals.get_by_id(user.hospital_id)
        await self._send_new_code(user, hospital.name if hospital else "your hospital")
        await self.uow.commit()

    async def _send_new_code(self, user: User, hospital_name: str) -> None:
        assert user.email is not None
        code = generate_verification_code()
        ttl = self.settings.verification_code_ttl_minutes
        await self.uow.email_verifications.add(
            EmailVerification(
                user_id=user.id,
                code_hash=hash_verification_code(code, self.settings),
                expires_at=utcnow() + timedelta(minutes=ttl),
            )
        )
        await self.email.send(
            EmailMessage(
                to=user.email,
                subject=f"Your verification code: {code}",
                text=(
                    f"Hello,\n\n"
                    f"Use this code to verify the email for {hospital_name}'s registration "
                    f"on Hospital Agent:\n\n"
                    f"    {code}\n\n"
                    f"The code expires in {ttl} minutes. "
                    f"If you didn't register, you can ignore this email.\n"
                ),
            )
        )
