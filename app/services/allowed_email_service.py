from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.models import AllowedEmail


def normalize_email(email: str) -> str:
    return email.strip().lower()


def is_email_allowed(db: Session, email: str) -> bool:
    normalized = normalize_email(email)
    return db.query(AllowedEmail).filter_by(email=normalized).first() is not None


def add_allowed_email(db: Session, email: str) -> AllowedEmail:
    normalized = normalize_email(email)
    record = db.query(AllowedEmail).filter_by(email=normalized).first()
    if record is not None:
        return record
    record = AllowedEmail(email=normalized)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def remove_allowed_email(db: Session, email: str) -> None:
    normalized = normalize_email(email)
    record = db.query(AllowedEmail).filter_by(email=normalized).first()
    if record is not None:
        db.delete(record)
        db.commit()


def list_allowed_emails(db: Session) -> list[AllowedEmail]:
    return db.query(AllowedEmail).order_by(AllowedEmail.email).all()


def sync_allowed_emails_from_file(db: Session, file_path: Path) -> None:
    if not file_path.exists():
        return
    for line in file_path.read_text().splitlines():
        email = line.strip()
        if email and not email.startswith("#"):
            add_allowed_email(db, email)
