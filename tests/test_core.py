import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import Settings
from app.services.event_limits import EventLimitError, ensure_event_count_allowed
from app.services.calendar_service import build_calendar_bytes
from app.models import Event, AvailabilityChoice


def test_settings_reads_max_events():
    settings = Settings()
    assert settings.max_events_per_poll == 30


def test_rejects_when_event_count_exceeds_limit():
    with pytest.raises(EventLimitError):
        ensure_event_count_allowed(31, 30)


def test_allows_event_count_within_limit():
    ensure_event_count_allowed(30, 30)
    ensure_event_count_allowed(1, 30)


def test_build_calendar_includes_yes_and_maybe_only():
    zone = ZoneInfo("America/Denver")
    events = [
        Event(id=1, poll_id=1, title="Match A", start_at=datetime(2026, 3, 1, 10, 0, tzinfo=zone), location="Court 1"),
        Event(id=2, poll_id=1, title="Match B", start_at=datetime(2026, 3, 2, 10, 0, tzinfo=zone), location="Court 2"),
        Event(id=3, poll_id=1, title="Match C", start_at=datetime(2026, 3, 3, 10, 0, tzinfo=zone), location="Court 3"),
    ]
    choices = {
        1: AvailabilityChoice.yes,
        2: AvailabilityChoice.maybe,
        3: AvailabilityChoice.no,
    }
    calendar_bytes = build_calendar_bytes(events, choices, "America/Denver")
    text = calendar_bytes.decode("utf-8")
    assert "Match A" in text
    assert "Match B" in text
    assert "Match C" not in text
