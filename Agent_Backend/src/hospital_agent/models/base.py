from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Column, DateTime, Enum
from sqlmodel import SQLModel

# Predictable constraint names, so migrations can drop/alter them later.
SQLModel.metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def utcnow() -> datetime:
    return datetime.now(UTC)


def created_at_column() -> Column[datetime]:
    return Column(DateTime(timezone=True), nullable=False, default=utcnow)


def updated_at_column() -> Column[datetime]:
    return Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)


def timestamp_column(nullable: bool = True) -> Column[datetime]:
    return Column(DateTime(timezone=True), nullable=nullable)


def str_enum_column(enum_cls: type[StrEnum]) -> Column[str]:
    """Stores enum *values* as VARCHAR, not a Postgres ENUM type.

    Adding a member later needs no ALTER TYPE migration.
    """
    return Column(
        Enum(
            enum_cls,
            native_enum=False,
            length=32,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
