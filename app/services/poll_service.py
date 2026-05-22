from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Poll


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
