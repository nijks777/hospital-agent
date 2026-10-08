import uuid
from datetime import datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel

from hospital_agent.models.base import (
    created_at_column,
    str_enum_column,
    timestamp_column,
    updated_at_column,
    utcnow,
)


class UserRole(StrEnum):
    PLATFORM_ADMIN = "platform_admin"
    HOSPITAL_ADMIN = "hospital_admin"


class User(SQLModel, table=True):
    __tablename__ = "users"  # pyright: ignore[reportAssignmentType]

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # Platform admins pick a username; hospital admins use their email as username.
    username: str = Field(max_length=255, unique=True, index=True)
    email: str | None = Field(default=None, max_length=255, unique=True)
    email_verified_at: datetime | None = Field(default=None, sa_column=timestamp_column())
    password_hash: str = Field(max_length=255)
    role: UserRole = Field(sa_column=str_enum_column(UserRole))
    hospital_id: uuid.UUID | None = Field(default=None, foreign_key="hospitals.id", index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utcnow, sa_column=created_at_column())
    updated_at: datetime = Field(default_factory=utcnow, sa_column=updated_at_column())
