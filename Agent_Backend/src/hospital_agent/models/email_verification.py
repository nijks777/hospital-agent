import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel

from hospital_agent.models.base import created_at_column, timestamp_column, utcnow


class EmailVerification(SQLModel, table=True):
    """A one-time code sent to a user's email. Only HMACs are stored.

    The code is bound to the registration that requested it (`registration_token_hash`):
    verifying needs the code (from the inbox) AND the token (held by that browser), so a
    second person re-registering the same email can never complete someone else's signup.
    """

    __tablename__ = "email_verifications"  # pyright: ignore[reportAssignmentType]

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, ondelete="CASCADE")
    code_hash: str = Field(max_length=64)
    registration_token_hash: str = Field(max_length=64)
    attempts: int = Field(default=0)
    expires_at: datetime = Field(sa_column=timestamp_column(nullable=False))
    consumed_at: datetime | None = Field(default=None, sa_column=timestamp_column())
    created_at: datetime = Field(default_factory=utcnow, sa_column=created_at_column())
