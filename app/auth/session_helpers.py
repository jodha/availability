from __future__ import annotations

from fastapi import Request

from app.config import get_settings
from app.models import User


def get_user_id(request: Request) -> int | None:
    value = request.session.get("user_id")
    return int(value) if value is not None else None


def get_pending_email(request: Request) -> str | None:
    return request.session.get("pending_email")


def set_pending_email(request: Request, email: str) -> None:
    request.session["pending_email"] = email.lower()


def clear_pending_email(request: Request) -> None:
    request.session.pop("pending_email", None)


def set_user_session(request: Request, user: User) -> None:
    request.session["user_id"] = user.id


def clear_user_session(request: Request) -> None:
    request.session.pop("user_id", None)


def is_admin_session(request: Request) -> bool:
    return request.session.get("admin") is True


def set_admin_session(request: Request) -> None:
    request.session["admin"] = True


def clear_admin_session(request: Request) -> None:
    request.session.pop("admin", None)


def admin_credentials_valid(username: str, password: str) -> bool:
    settings = get_settings()
    return username == settings.admin_username and password == settings.admin_password
