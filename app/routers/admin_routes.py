from __future__ import annotations

from pathlib import Path

from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.session_helpers import (
    admin_credentials_valid,
    clear_admin_session,
    clear_user_session,
    get_user_id,
    is_admin_session,
    set_admin_session,
    set_user_session,
)
from app.config import get_settings
from app.database import get_db
from app.models import AvailabilityChoice, Event, Poll, User
from app.services.availability_service import matrix_for_poll, save_availability
from app.services.event_limits import EventLimitError, ensure_event_count_allowed
from app.services.poll_service import create_poll, get_active_poll, parse_start_at

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


def _redirect(url: str, message: str | None = None) -> RedirectResponse:
    target = f"{url}?message={quote(message)}" if message else url
    return RedirectResponse(target, status_code=303)


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
    if not is_admin_session(request):
        return RedirectResponse("/admin/login", status_code=303)
    settings = get_settings()
    poll = get_active_poll(db)
    users = db.query(User).order_by(User.display_name).all()
    events = poll.events if poll else []
    matrix = matrix_for_poll(db, events) if poll else {}
    return templates.TemplateResponse(
        request,
        "admin_dashboard.html",
        {
            "app_name": settings.app_name,
            "poll": poll,
            "events": events,
            "users": users,
            "matrix": matrix,
            "invite_code": settings.invite_code,
            "max_events": settings.max_events_per_poll,
            "timezone": settings.timezone,
        },
    )


@router.post("/admin/polls")
def admin_create_poll(request: Request, title: str = Form(...), db: Session = Depends(get_db)):
    if not is_admin_session(request):
        return RedirectResponse("/admin/login", status_code=303)
    create_poll(db, title)
    return _redirect("/admin", "Poll created")


@router.post("/admin/events")
def admin_create_event(
    request: Request,
    title: str = Form(...),
    start_at: str = Form(...),
    location: str = Form(...),
    db: Session = Depends(get_db),
):
    if not is_admin_session(request):
        return RedirectResponse("/admin/login", status_code=303)
    poll = get_active_poll(db)
    if poll is None:
        return _redirect("/admin", "Create a poll first")
    settings = get_settings()
    try:
        ensure_event_count_allowed(len(poll.events) + 1, settings.max_events_per_poll)
    except EventLimitError as error:
        return _redirect("/admin", str(error))
    event = Event(
        poll_id=poll.id,
        title=title.strip(),
        start_at=parse_start_at(start_at, settings.timezone),
        location=location.strip(),
    )
    db.add(event)
    db.commit()
    return _redirect("/admin", "Event added")


@router.post("/admin/events/{event_id}/delete")
def admin_delete_event(event_id: int, request: Request, db: Session = Depends(get_db)):
    if not is_admin_session(request):
        return RedirectResponse("/admin/login", status_code=303)
    event = db.query(Event).filter_by(id=event_id).first()
    if event is not None:
        db.delete(event)
        db.commit()
    return _redirect("/admin", "Event deleted")
