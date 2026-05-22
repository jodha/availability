import smtplib
from email.message import EmailMessage

from app.config import Settings


def _send_email(settings: Settings, recipient: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)


def send_calendar_email(settings: Settings, recipient: str, calendar_bytes: bytes) -> None:
    message = EmailMessage()
    message["Subject"] = f"{settings.app_name} calendar events"
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message.set_content("Attached are your selected events.")
    message.add_attachment(
        calendar_bytes,
        maintype="text",
        subtype="calendar",
        filename="availability.ics",
    )
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)


def send_password_reset_email(settings: Settings, recipient: str, reset_url: str) -> None:
    body = f"Reset your password:\n\n{reset_url}\n\nThis link expires in one hour."
    _send_email(settings, recipient, f"{settings.app_name} password reset", body)
