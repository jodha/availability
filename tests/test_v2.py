from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.orm import sessionmaker

from app.models import Base, Event, Location, build_engine, format_location
from app.services.allowed_email_service import add_allowed_email, is_email_allowed
from app.services.calendar_service import build_imip_invite_bytes


@pytest.fixture
def db_session():
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def test_allowed_email_check(db_session):
    add_allowed_email(db_session, "alex@example.com")
    assert is_email_allowed(db_session, "alex@example.com") is True
    assert is_email_allowed(db_session, "unknown@example.com") is False


def test_format_location():
    location = Location(venue_name="Court 1", address="123 Main St, Denver, CO")
    assert format_location(location) == "Court 1, 123 Main St, Denver, CO"


def test_imip_invite_uses_request_method(db_session):
    zone = ZoneInfo("America/Denver")
    location = Location(id=1, venue_name="Court 1", address="123 Main St")
    event = Event(
        id=1,
        poll_id=1,
        location_id=1,
        title="Match A",
        start_at=datetime(2026, 3, 1, 10, 0, tzinfo=zone),
        calendar_sequence=0,
    )
    event.location = location
    calendar_bytes = build_imip_invite_bytes(event, "alex@example.com", "admin@example.com", "America/Denver")
    text = calendar_bytes.decode("utf-8")
    assert "METHOD:REQUEST" in text
    assert "Court 1" in text
    assert "123 Main St" in text
