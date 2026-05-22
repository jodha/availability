from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.auth.passwords import hash_password
from app.models import PasswordResetToken, User


def create_reset_token(
    db: Session,
    user_id: int,
    expires_in: timedelta = timedelta(hours=1),
) -> str:
    token = secrets.token_urlsafe(32)
    record = PasswordResetToken(
        user_id=user_id,
        token=token,
        expires_at=datetime.now(timezone.utc) + expires_in,
    )
    db.add(record)
    db.commit()
    return token


def token_is_valid(expires_at: datetime) -> bool:
    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at > now


def find_valid_token(db: Session, token: str) -> PasswordResetToken | None:
    record = db.query(PasswordResetToken).filter_by(token=token).first()
    if record is None:
        return None
    if not token_is_valid(record.expires_at):
        return None
    return record


def reset_user_password(db: Session, token: str, new_password: str) -> User:
    record = find_valid_token(db, token)
    if record is None:
        raise ValueError("Invalid or expired reset link")
    user = db.query(User).filter_by(id=record.user_id).first()
    if user is None:
        raise ValueError("User not found")
    user.password_hash = hash_password(new_password)
    db.delete(record)
    db.commit()
    db.refresh(user)
    return user


def admin_reset_password(db: Session, user_id: int, new_password: str) -> User:
    user = db.query(User).filter_by(id=user_id).first()
    if user is None:
        raise ValueError("User not found")
    user.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user
