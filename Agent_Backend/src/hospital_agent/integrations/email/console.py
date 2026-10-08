import logging

from hospital_agent.integrations.email.port import EmailMessage

logger = logging.getLogger(__name__)


class ConsoleEmailSender:
    """Development adapter: prints the email to the server log instead of sending it."""

    async def send(self, message: EmailMessage) -> None:
        logger.warning(
            "EMAIL (console backend, not sent)\nTo: %s\nSubject: %s\n\n%s",
            message.to,
            message.subject,
            message.text,
        )
