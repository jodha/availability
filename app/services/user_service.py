from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import User


def find_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter_by(email=email.lower()).first()


def create_user(db: Session, email: str, display_name: str) -> User:
    if find_user_by_email(db, email):
        raise ValueError("Email already registered")
    user = User(email=email.lower(), display_name=display_name.strip())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
