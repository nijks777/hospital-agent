from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    text: str


class EmailDeliveryError(Exception):
    """The provider could not send the message."""


class EmailSender(Protocol):
    """Port: anything that can deliver an email. Services depend on this, never on SMTP."""

    async def send(self, message: EmailMessage) -> None: ...
