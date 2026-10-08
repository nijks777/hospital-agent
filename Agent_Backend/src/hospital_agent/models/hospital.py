import uuid
from datetime import datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel

from hospital_agent.models.base import (
    created_at_column,
    str_enum_column,
    updated_at_column,
    utcnow,
)


class HospitalStatus(StrEnum):
    PENDING_VERIFICATION = "pending_verification"  # registered, email not verified yet
    PENDING_REVIEW = "pending_review"  # email verified, waiting for platform admin
    ACTIVE = "active"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


# State machine: the only moves a hospital's status may make.
ALLOWED_TRANSITIONS: dict[HospitalStatus, set[HospitalStatus]] = {
    HospitalStatus.PENDING_VERIFICATION: {HospitalStatus.PENDING_REVIEW},
    HospitalStatus.PENDING_REVIEW: {HospitalStatus.ACTIVE, HospitalStatus.REJECTED},
    HospitalStatus.ACTIVE: {HospitalStatus.SUSPENDED},
    HospitalStatus.SUSPENDED: {HospitalStatus.ACTIVE},
    HospitalStatus.REJECTED: set(),
}


class InvalidStatusTransitionError(Exception):
    def __init__(self, current: HospitalStatus, target: HospitalStatus) -> None:
        super().__init__(f"Cannot move hospital from {current} to {target}")


class Hospital(SQLModel, table=True):
    __tablename__ = "hospitals"  # pyright: ignore[reportAssignmentType]

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=200)
    city: str = Field(max_length=100)
    contact_name: str = Field(max_length=120)
    contact_phone: str = Field(max_length=20)
    status: HospitalStatus = Field(sa_column=str_enum_column(HospitalStatus))
    created_at: datetime = Field(default_factory=utcnow, sa_column=created_at_column())
    updated_at: datetime = Field(default_factory=utcnow, sa_column=updated_at_column())

    def transition_to(self, target: HospitalStatus) -> None:
        if target not in ALLOWED_TRANSITIONS[self.status]:
            raise InvalidStatusTransitionError(self.status, target)
        self.status = target
