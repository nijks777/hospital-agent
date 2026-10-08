import uuid

from hospital_agent.core.config import Settings
from hospital_agent.core.security import create_access_token, hash_password, verify_password
from hospital_agent.db.unit_of_work import UnitOfWork
from hospital_agent.models.hospital import HospitalStatus
from hospital_agent.models.user import User, UserRole


class InvalidCredentialsError(Exception):
    pass


class HospitalNotActiveError(Exception):
    """Correct password, but the user's hospital can't use the platform (yet)."""

    def __init__(self, status: HospitalStatus) -> None:
        super().__init__(status)
        self.status = status


class UsernameTakenError(Exception):
    pass


class AuthService:
    def __init__(self, uow: UnitOfWork, settings: Settings) -> None:
        self.uow = uow
        self.settings = settings

    async def login(self, username: str, password: str) -> tuple[User, str]:
        """Returns the user and a signed access token. Same error for every credential failure."""
        user = await self.uow.users.get_by_username(username.strip().lower())
        password_ok = verify_password(password, user.password_hash if user else None)
        if user is None or not password_ok or not user.is_active:
            raise InvalidCredentialsError

        if user.role == UserRole.HOSPITAL_ADMIN:
            hospital = await self.uow.hospitals.get_by_id(user.hospital_id)
            if hospital is None:
                raise InvalidCredentialsError
            if hospital.status != HospitalStatus.ACTIVE:
                raise HospitalNotActiveError(hospital.status)

        return user, create_access_token(user.id, user.role, self.settings)

    async def get_active_user(self, user_id: uuid.UUID) -> User | None:
        """Checked on every authenticated request, not just at login: suspending a user or
        their hospital takes effect immediately, even though their token is still valid."""
        user = await self.uow.users.get_by_id(user_id)
        if user is None or not user.is_active:
            return None
        if user.role == UserRole.HOSPITAL_ADMIN:
            hospital = await self.uow.hospitals.get_by_id(user.hospital_id)
            if hospital is None or hospital.status != HospitalStatus.ACTIVE:
                return None
        return user

    async def create_platform_admin(self, username: str, password: str) -> User:
        username = username.strip().lower()
        if await self.uow.users.get_by_username(username):
            raise UsernameTakenError(username)
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=UserRole.PLATFORM_ADMIN,
        )
        await self.uow.users.add(user)
        await self.uow.commit()
        return user
