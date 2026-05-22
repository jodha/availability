import pytest

from app.services.event_limits import EventLimitError, ensure_event_count_allowed


def test_rejects_when_event_count_exceeds_limit():
    with pytest.raises(EventLimitError):
        ensure_event_count_allowed(31, 30)


def test_allows_event_count_within_limit():
    ensure_event_count_allowed(30, 30)
    ensure_event_count_allowed(1, 30)
