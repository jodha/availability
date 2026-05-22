from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Availability, AvailabilityChoice, Event


def save_availability(db: Session, user_id: int, event_id: int, choice: AvailabilityChoice) -> None:
    record = db.query(Availability).filter_by(user_id=user_id, event_id=event_id).first()
    if record is None:
        record = Availability(user_id=user_id, event_id=event_id, choice=choice)
        db.add(record)
    else:
        record.choice = choice
    db.commit()


def choices_for_user(db: Session, user_id: int, event_ids: list[int]) -> dict[int, AvailabilityChoice]:
    rows = db.query(Availability).filter(
        Availability.user_id == user_id,
        Availability.event_id.in_(event_ids),
    ).all()
    return {row.event_id: row.choice for row in rows}


def matrix_for_poll(db: Session, events: list[Event]) -> dict[int, dict[int, AvailabilityChoice]]:
    event_ids = [event.id for event in events]
    rows = db.query(Availability).filter(Availability.event_id.in_(event_ids)).all()
    matrix: dict[int, dict[int, AvailabilityChoice]] = {}
    for row in rows:
        matrix.setdefault(row.user_id, {})[row.event_id] = row.choice
    return matrix
