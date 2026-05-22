from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Event, Location


def create_location(db: Session, venue_name: str, address: str) -> Location:
    location = Location(venue_name=venue_name.strip(), address=address.strip())
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


def list_locations(db: Session) -> list[Location]:
    return db.query(Location).order_by(Location.venue_name).all()


def update_location(db: Session, location_id: int, venue_name: str, address: str) -> Location:
    location = db.query(Location).filter_by(id=location_id).first()
    if location is None:
        raise ValueError("Location not found")
    location.venue_name = venue_name.strip()
    location.address = address.strip()
    db.commit()
    db.refresh(location)
    return location


def delete_location(db: Session, location_id: int) -> None:
    location = db.query(Location).filter_by(id=location_id).first()
    if location is None:
        return
    db.delete(location)
    db.commit()


def events_for_location(db: Session, location_id: int) -> list[Event]:
    return db.query(Event).filter_by(location_id=location_id).order_by(Event.start_at).all()


def increment_event_sequences(db: Session, events: list[Event]) -> None:
    for event in events:
        event.calendar_sequence += 1
    db.commit()
