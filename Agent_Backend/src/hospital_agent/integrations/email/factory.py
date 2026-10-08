from hospital_agent.core.config import Settings
from hospital_agent.integrations.email.console import ConsoleEmailSender
from hospital_agent.integrations.email.port import EmailSender
from hospital_agent.integrations.email.smtp import SmtpEmailSender


def create_email_sender(settings: Settings) -> EmailSender:
    """Factory: picks the adapter named in config. A new provider = one adapter + one branch."""
    if settings.email_backend == "smtp":
        return SmtpEmailSender(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            sender=settings.email_from,
        )
    return ConsoleEmailSender()
