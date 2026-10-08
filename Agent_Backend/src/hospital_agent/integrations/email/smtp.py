from email.message import EmailMessage as MimeMessage

import aiosmtplib

from hospital_agent.integrations.email.port import EmailDeliveryError, EmailMessage


class SmtpEmailSender:
    """Sends through any SMTP server. With Gmail: smtp.gmail.com:587 + an app password."""

    def __init__(self, host: str, port: int, username: str, password: str, sender: str) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender = sender

    async def send(self, message: EmailMessage) -> None:
        mime = MimeMessage()
        mime["From"] = self.sender
        mime["To"] = message.to
        mime["Subject"] = message.subject
        mime.set_content(message.text)
        try:
            await aiosmtplib.send(
                mime,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                start_tls=True,
                timeout=15,
            )
        except aiosmtplib.SMTPException as exc:
            raise EmailDeliveryError(str(exc)) from exc
