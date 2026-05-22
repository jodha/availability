from __future__ import annotations

from datetime import timedelta
from io import BytesIO
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event as IcsEvent

from app.models import AvailabilityChoice, Event


def build_calendar_bytes(
    events: list[Event],
    choices: dict[int, AvailabilityChoice],
    timezone_name: str,
) -> bytes:
    calendar = Calendar()
    calendar.add("prodid", "-//Availability//EN")
    calendar.add("version", "2.0")
    for event in events:
        choice = choices.get(event.id)
        if choice not in (AvailabilityChoice.yes, AvailabilityChoice.maybe):
            continue
        calendar.add("component", _build_event_component(event, timezone_name))
    buffer = BytesIO()
    buffer.write(calendar.to_ical())
    return buffer.getvalue()


def _build_event_component(event: Event, timezone_name: str) -> IcsEvent:
    ics_event = IcsEvent()
    ics_event.add("summary", event.title)
    ics_event.add("dtstart", event.start_at)
    ics_event.add("dtend", event.start_at + timedelta(hours=2))
    ics_event.add("location", event.location)
    ics_event.add("uid", f"availability-event-{event.id}@availability")
    ics_event.add("dtstamp", event.start_at.astimezone(ZoneInfo(timezone_name)))
    return ics_event
