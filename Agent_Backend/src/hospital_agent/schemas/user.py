import uuid

from pydantic import BaseModel

from hospital_agent.models.user import UserRole


class UserRead(BaseModel):
    """Public view of a user. Deliberately has no password_hash."""

    id: uuid.UUID
    username: str
    email: str | None
    role: UserRole
    hospital_id: uuid.UUID | None
