"""In-memory stand-ins for the database and email, so service logic is tested without I/O."""

import uuid

from hospital_agent.integrations.email.port import EmailDeliveryError, EmailMessage
from hospital_agent.models.email_verification import EmailVerification
from hospital_agent.models.hospital import Hospital
from hospital_agent.models.user import User


class FakeUserRepository:
    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, User] = {}

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.rows.get(user_id)

    async def get_by_username(self, username: str) -> User | None:
        return next((u for u in self.rows.values() if u.username == username), None)

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.rows.values() if u.email == email), None)

    async def add(self, user: User) -> User:
        self.rows[user.id] = user
        return user


class FakeHospitalRepository:
    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, Hospital] = {}

    async def get_by_id(self, hospital_id: uuid.UUID | None) -> Hospital | None:
        return self.rows.get(hospital_id) if hospital_id else None

    async def add(self, hospital: Hospital) -> Hospital:
        self.rows[hospital.id] = hospital
        return hospital


class FakeEmailVerificationRepository:
    def __init__(self) -> None:
        self.rows: list[EmailVerification] = []

    async def get_latest_for_user(self, user_id: uuid.UUID) -> EmailVerification | None:
        mine = [v for v in self.rows if v.user_id == user_id]
        return mine[-1] if mine else None

    async def add(self, verification: EmailVerification) -> EmailVerification:
        self.rows.append(verification)
        return verification


class FakeUnitOfWork:
    def __init__(self, *users: User, hospitals: tuple[Hospital, ...] = ()) -> None:
        self.users = FakeUserRepository()
        self.hospitals = FakeHospitalRepository()
        self.email_verifications = FakeEmailVerificationRepository()
        for u in users:
            self.users.rows[u.id] = u
        for h in hospitals:
            self.hospitals.rows[h.id] = h
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1


class FakeEmailSender:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.sent: list[EmailMessage] = []

    async def send(self, message: EmailMessage) -> None:
        if self.fail:
            raise EmailDeliveryError("smtp down")
        self.sent.append(message)

    def last_code(self) -> str:
        """The 6-digit code from the most recent email's subject line."""
        return self.sent[-1].subject.rsplit(" ", 1)[-1]
