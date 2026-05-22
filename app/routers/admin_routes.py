from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.auth.session_helpers import admin_credentials_valid, clear_admin_session, is_admin_session, set_admin_session
from app.config import get_settings
from app.database import get_db
from app.models import Availability, Event, User
from app.services.allowed_email_service import add_allowed_email, list_allowed_emails, remove_allowed_email
from app.services.availability_service import matrix_for_poll
from app.services.calendar_delivery_service import send_invites_for_events
from app.services.event_limits import EventLimitError, ensure_event_count_allowed
from app.services.location_service import (
    create_location,
    delete_location,
    events_for_location,
    list_locations,
    update_location,
)
from app.services.poll_service import create_poll, get_active_poll, parse_start_at

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


def _redirect(url: str, message: str | None = None) -> RedirectResponse:
    target = f"{url}?message={quote(message)}" if message else url
    return RedirectResponse(target, status_code=303)


def _require_admin(request: Request) -> RedirectResponse | None:
    if not is_admin_session(request):
        return RedirectResponse("/admin/login", status_code=303)
    return None


def _resolve_location_id(
    db: Session,
    location_id: str,
    new_venue_name: str,
    new_address: str,
) -> int:
    if new_venue_name.strip() and new_address.strip():
        return create_location(db, new_venue_name, new_address).id
    if location_id.strip():
        return int(location_id)
    raise ValueError("Select a location or add a new one")


@router.get("/admin/login", response_class=HTMLResponse)
def admin_login_page(request: Request):
    settings = get_settings()
    return templates.TemplateResponse(request, "admin_login.html", {"app_name": settings.app_name})


@router.post("/admin/login")
def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    if not admin_credentials_valid(username, password):
        return _redirect("/admin/login", "Invalid admin credentials")
    set_admin_session(request)
    return _redirect("/admin")


@router.post("/admin/logout")
def admin_logout(request: Request):
    clear_admin_session(request)
    return _redirect("/admin/login")


@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    if _require_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    settings = get_settings()
    poll = get_active_poll(db)
    users = db.query(User).order_by(User.display_name).all()
    events = []
    if poll:
        events = (
            db.query(Event)
            .options(joinedload(Event.location))
            .filter_by(poll_id=poll.id)
            .order_by(Event.start_at)
            .all()
        )
    matrix = matrix_for_poll(db, events) if poll else {}
    locations = list_locations(db)
    allowed = list_allowed_emails(db)
    updated_location_id = request.query_params.get("location_updated")
    affected_events = []
    if updated_location_id:
        affected_events = events_for_location(db, int(updated_location_id))
    return templates.TemplateResponse(
        request,
        "admin_dashboard.html",
        {
            "app_name": settings.app_name,
            "poll": poll,
            "events": events,
            "users": users,
            "matrix": matrix,
            "locations": locations,
            "allowed_emails": allowed,
            "base_url": settings.base_url,
            "max_events": settings.max_events_per_poll,
            "timezone": settings.timezone,
            "updated_location_id": updated_location_id,
            "affected_events": affected_events,
        },
    )


@router.post("/admin/polls")
def admin_create_poll(request: Request, title: str = Form(...), db: Session = Depends(get_db)):
    if _require_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    create_poll(db, title)
    return _redirect("/admin", "Poll created")


@router.post("/admin/locations")
def admin_create_location(
    request: Request,
    venue_name: str = Form(...),
    address: str = Form(...),
    db: Session = Depends(get_db),
):
    if _require_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    create_location(db, venue_name, address)
    return _redirect("/admin", "Location added")


@router.post("/admin/locations/{location_id}/update")
def admin_update_location(
    location_id: int,
    request: Request,
    venue_name: str = Form(...),
    address: str = Form(...),
    db: Session = Depends(get_db),
):
    if _require_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    update_location(db, location_id, venue_name, address)
    return RedirectResponse(f"/admin?location_updated={location_id}", status_code=303)


@router.post("/admin/locations/{location_id}/delete")
def admin_delete_location(location_id: int, request: Request, db: Session = Depends(get_db)):
    if _require_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    delete_location(db, location_id)
    return _redirect("/admin", "Location deleted")


@router.post("/admin/locations/{location_id}/resend-calendars")
def admin_resend_calendars(location_id: int, request: Request, db: Session = Depends(get_db)):
    if _require_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    settings = get_settings()
    events = (
        db.query(Event)
        .options(
            joinedload(Event.location),
            joinedload(Event.availabilities).joinedload(Availability.user),
        )
        .filter_by(location_id=location_id)
        .all()
    )
    count = send_invites_for_events(settings, db, events, bump_sequence=True)
    return _redirect("/admin", f"Sent {count} updated calendar invite(s)")


@router.post("/admin/allowed-emails")
def admin_add_allowed_email(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
    if _require_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    add_allowed_email(db, email)
    return _redirect("/admin", "Email added")


@router.post("/admin/allowed-emails/delete")
def admin_remove_allowed_email(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
    if _require_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    remove_allowed_email(db, email)
    return _redirect("/admin", "Email removed")


@router.post("/admin/events")
def admin_create_event(
    request: Request,
    title: str = Form(...),
    start_at: str = Form(...),
    location_id: str = Form(""),
    new_venue_name: str = Form(""),
    new_address: str = Form(""),
    db: Session = Depends(get_db),
):
    if _require_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    poll = get_active_poll(db)
    if poll is None:
        return _redirect("/admin", "Create a poll first")
    settings = get_settings()
    try:
        ensure_event_count_allowed(len(poll.events) + 1, settings.max_events_per_poll)
        resolved_location_id = _resolve_location_id(db, location_id, new_venue_name, new_address)
    except (EventLimitError, ValueError) as error:
        return _redirect("/admin", str(error))
    event = Event(
        poll_id=poll.id,
        title=title.strip(),
        start_at=parse_start_at(start_at, settings.timezone),
        location_id=resolved_location_id,
    )
    db.add(event)
    db.commit()
    return _redirect("/admin", "Event added")


@router.post("/admin/events/{event_id}/delete")
def admin_delete_event(event_id: int, request: Request, db: Session = Depends(get_db)):
    if _require_admin(request):
        return RedirectResponse("/admin/login", status_code=303)
    event = db.query(Event).filter_by(id=event_id).first()
    if event is not None:
        db.delete(event)
        db.commit()
    return _redirect("/admin", "Event deleted")
