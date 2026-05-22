from __future__ import annotations

from datetime import datetime, timedelta
from io import BytesIO
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event as IcsEvent, vCalAddress

from app.models import Event, format_location


def build_imip_invite_bytes(
    event: Event,
    attendee_email: str,
    organizer_email: str,
    timezone_name: str,
) -> bytes:
    calendar = Calendar()
    calendar.add("method", "REQUEST")
    calendar.add("prodid", "-//Availability//EN")
    calendar.add("version", "2.0")
    calendar.add_component(_build_request_component(event, attendee_email, organizer_email, timezone_name))
    buffer = BytesIO()
    buffer.write(calendar.to_ical())
    return buffer.getvalue()


def invite_subject(app_name: str, event_title: str) -> str:
    return f"{app_name}: {event_title}"


def _build_request_component(
    event: Event,
    attendee_email: str,
    organizer_email: str,
    timezone_name: str,
) -> IcsEvent:
    ics_event = IcsEvent()
    ics_event.add("method", "REQUEST")
    ics_event.add("status", "CONFIRMED")
    ics_event.add("summary", event.title)
    ics_event.add("dtstart", event.start_at)
    ics_event.add("dtend", event.start_at + timedelta(hours=2))
    ics_event.add("location", format_location(event.location))
    ics_event.add("uid", f"availability-event-{event.id}@availability")
    ics_event.add("sequence", event.calendar_sequence)
    ics_event.add("dtstamp", datetime.now(ZoneInfo(timezone_name)))
    ics_event.add("organizer", _mailto(organizer_email))
    ics_event.add("attendee", _mailto(attendee_email), parameters={"RSVP": "TRUE"})
    return ics_event


def _mailto(email: str) -> vCalAddress:
    address = vCalAddress(f"mailto:{email}")
    address.params["cn"] = email
    return address
