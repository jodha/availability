from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.auth.session_helpers import (
    clear_pending_email,
    clear_user_session,
    get_pending_email,
    get_user_id,
    set_pending_email,
    set_user_session,
)
from app.config import get_settings
from app.database import get_db
from app.models import AvailabilityChoice, Event, User
from app.services.allowed_email_service import is_email_allowed
from app.services.availability_service import choices_for_user, matrix_for_poll, save_availability
from app.services.calendar_delivery_service import send_user_calendar_invites
from app.services.poll_service import get_active_poll
from app.services.user_service import create_user, find_user_by_email

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


def _redirect(url: str, message: str | None = None) -> RedirectResponse:
    target = f"{url}?message={quote(message)}" if message else url
    return RedirectResponse(target, status_code=303)


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    settings = get_settings()
    poll = get_active_poll(db)
    user_id = get_user_id(request)
    return templates.TemplateResponse(
        request,
        "home.html",
        {"app_name": settings.app_name, "poll": poll, "logged_in": user_id is not None},
    )


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    settings = get_settings()
    return templates.TemplateResponse(request, "login.html", {"app_name": settings.app_name})


@router.post("/login")
def login(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
    if not is_email_allowed(db, email):
        return _redirect("/login", "Your email is not authorized")
    user = find_user_by_email(db, email)
    if user is None:
        set_pending_email(request, email)
        return _redirect("/set-display-name")
    set_user_session(request, user)
    return _redirect("/poll")


@router.get("/set-display-name", response_class=HTMLResponse)
def display_name_page(request: Request):
    if get_pending_email(request) is None:
        return RedirectResponse("/login", status_code=303)
    settings = get_settings()
    return templates.TemplateResponse(request, "set_display_name.html", {"app_name": settings.app_name})


@router.post("/set-display-name")
def set_display_name(request: Request, display_name: str = Form(...), db: Session = Depends(get_db)):
    email = get_pending_email(request)
    if email is None:
        return RedirectResponse("/login", status_code=303)
    if not is_email_allowed(db, email):
        return _redirect("/login", "Your email is not authorized")
    user = create_user(db, email, display_name)
    clear_pending_email(request)
    set_user_session(request, user)
    return _redirect("/poll")


@router.post("/logout")
def logout(request: Request):
    clear_user_session(request)
    clear_pending_email(request)
    return _redirect("/")


@router.get("/poll", response_class=HTMLResponse)
def poll_page(request: Request, db: Session = Depends(get_db)):
    user_id = get_user_id(request)
    if user_id is None:
        return RedirectResponse("/login", status_code=303)
    settings = get_settings()
    poll = get_active_poll(db)
    user = db.query(User).filter_by(id=user_id).first()
    events = []
    if poll:
        events = (
            db.query(Event)
            .options(joinedload(Event.location))
            .filter_by(poll_id=poll.id)
            .order_by(Event.start_at)
            .all()
        )
    event_ids = [event.id for event in events]
    own_choices = choices_for_user(db, user_id, event_ids)
    users = db.query(User).order_by(User.display_name).all()
    matrix = matrix_for_poll(db, events) if poll else {}
    return templates.TemplateResponse(
        request,
        "poll.html",
        {
            "app_name": settings.app_name,
            "poll": poll,
            "events": events,
            "user": user,
            "own_choices": own_choices,
            "users": users,
            "matrix": matrix,
            "choices": AvailabilityChoice,
            "timezone": settings.timezone,
        },
    )


@router.post("/poll/availability")
def set_availability(
    request: Request,
    event_id: int = Form(...),
    choice: str = Form(...),
    db: Session = Depends(get_db),
):
    user_id = get_user_id(request)
    if user_id is None:
        return RedirectResponse("/login", status_code=303)
    save_availability(db, user_id, event_id, AvailabilityChoice(choice))
    return _redirect("/poll")


@router.post("/poll/email-calendar")
def email_calendar(request: Request, db: Session = Depends(get_db)):
    user_id = get_user_id(request)
    if user_id is None:
        return RedirectResponse("/login", status_code=303)
    settings = get_settings()
    poll = get_active_poll(db)
    if poll is None:
        return _redirect("/poll", "No active poll")
    user = db.query(User).filter_by(id=user_id).first()
    events = (
        db.query(Event)
        .options(joinedload(Event.location))
        .filter_by(poll_id=poll.id)
        .order_by(Event.start_at)
        .all()
    )
    count = send_user_calendar_invites(settings, db, user, events)
    if count == 0:
        return _redirect("/poll", "No Yes or Maybe events to send")
    return _redirect("/poll", f"Sent {count} calendar invite(s)")
