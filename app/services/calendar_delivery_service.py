from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import Settings
from app.models import AvailabilityChoice, Event, User
from app.services.availability_service import choices_for_user
from app.services.calendar_service import build_imip_invite_bytes, invite_subject
from app.services.email_service import send_imip_invite_email
from app.services.location_service import increment_event_sequences


def send_invites_for_events(
    settings: Settings,
    db: Session,
    events: list[Event],
    bump_sequence: bool,
) -> int:
    if bump_sequence:
        increment_event_sequences(db, events)
        for event in events:
            db.refresh(event)
    sent = 0
    for event in events:
        sent += _send_event_invites_to_all_yes_maybe(settings, event)
    return sent


def send_user_calendar_invites(
    settings: Settings,
    db: Session,
    user: User,
    events: list[Event],
) -> int:
    event_ids = [event.id for event in events]
    choices = choices_for_user(db, user.id, event_ids)
    count = 0
    for event in events:
        choice = choices.get(event.id)
        if choice not in (AvailabilityChoice.yes, AvailabilityChoice.maybe):
            continue
        calendar_bytes = build_imip_invite_bytes(
            event,
            user.email,
            settings.smtp_from,
            settings.timezone,
        )
        send_imip_invite_email(
            settings,
            user.email,
            invite_subject(settings.app_name, event.title),
            calendar_bytes,
        )
        count += 1
    return count


def _send_event_invites_to_all_yes_maybe(settings: Settings, event: Event) -> int:
    count = 0
    for row in event.availabilities:
        if row.choice not in (AvailabilityChoice.yes, AvailabilityChoice.maybe):
            continue
        calendar_bytes = build_imip_invite_bytes(
            event,
            row.user.email,
            settings.smtp_from,
            settings.timezone,
        )
        send_imip_invite_email(
            settings,
            row.user.email,
            invite_subject(settings.app_name, event.title),
            calendar_bytes,
        )
        count += 1
    return count
