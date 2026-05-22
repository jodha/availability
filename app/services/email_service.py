from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.config import Settings


def send_imip_invite_email(
    settings: Settings,
    recipient: str,
    subject: str,
    calendar_bytes: bytes,
) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message.set_content("You have a calendar invitation.")
    message.add_attachment(
        calendar_bytes,
        maintype="text",
        subtype="calendar",
        filename="invite.ics",
        params={"method": "REQUEST", "charset": "UTF-8"},
    )
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)
