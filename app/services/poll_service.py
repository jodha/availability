from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.auth.passwords import hash_password, verify_password
from app.auth.session_helpers import invite_code_valid
from app.models import Poll, User


def find_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter_by(email=email.lower()).first()


def create_user(db: Session, email: str, password: str, display_name: str, invite_code: str) -> User:
    if not invite_code_valid(invite_code):
        raise ValueError("Invalid invite code")
    if find_user_by_email(db, email):
        raise ValueError("Email already registered")
    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        display_name=display_name.strip(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = find_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def get_active_poll(db: Session) -> Poll | None:
    return db.query(Poll).filter_by(is_active=True).order_by(Poll.id.desc()).first()


def create_poll(db: Session, title: str) -> Poll:
    db.query(Poll).update({Poll.is_active: False})
    poll = Poll(title=title.strip(), is_active=True)
    db.add(poll)
    db.commit()
    db.refresh(poll)
    return poll


def parse_start_at(raw_value: str, timezone_name: str) -> datetime:
    from zoneinfo import ZoneInfo

    parsed = datetime.fromisoformat(raw_value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo(timezone_name))
    return parsed
