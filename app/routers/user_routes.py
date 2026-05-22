from __future__ import annotations

from pathlib import Path

from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.session_helpers import clear_user_session, get_user_id, set_user_session
from app.config import get_settings
from app.database import get_db
from app.models import AvailabilityChoice, User
from app.services.availability_service import choices_for_user, matrix_for_poll, save_availability
from app.services.calendar_service import build_calendar_bytes
from app.services.email_service import send_calendar_email
from app.services.poll_service import authenticate_user, create_user, get_active_poll

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


@router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    settings = get_settings()
    return templates.TemplateResponse(request, "signup.html", {"app_name": settings.app_name})


@router.post("/signup")
def signup(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    display_name: str = Form(...),
    invite_code: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        user = create_user(db, email, password, display_name, invite_code)
    except ValueError as error:
        return _redirect("/signup", str(error))
    set_user_session(request, user)
    return _redirect("/poll")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    settings = get_settings()
    return templates.TemplateResponse(request, "login.html", {"app_name": settings.app_name})


@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = authenticate_user(db, email, password)
    if user is None:
        return _redirect("/login", "Invalid email or password")
    set_user_session(request, user)
    return _redirect("/poll")


@router.post("/logout")
def logout(request: Request):
    clear_user_session(request)
    return _redirect("/")


@router.get("/poll", response_class=HTMLResponse)
def poll_page(request: Request, db: Session = Depends(get_db)):
    user_id = get_user_id(request)
    if user_id is None:
        return RedirectResponse("/login", status_code=303)
    settings = get_settings()
    poll = get_active_poll(db)
    user = db.query(User).filter_by(id=user_id).first()
    events = poll.events if poll else []
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
    events = poll.events
    event_ids = [event.id for event in events]
    own_choices = choices_for_user(db, user_id, event_ids)
    calendar_bytes = build_calendar_bytes(events, own_choices, settings.timezone)
    send_calendar_email(settings, user.email, calendar_bytes)
    return _redirect("/poll", "Calendar email sent")
