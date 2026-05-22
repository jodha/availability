from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.database import get_session_factory
from app.routers.admin_routes import router as admin_router
from app.routers.user_routes import router as user_router
from app.services.allowed_email_service import sync_allowed_emails_from_file


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    session = get_session_factory()()
    try:
        sync_allowed_emails_from_file(session, settings.allowed_emails_path)
    finally:
        session.close()
    yield


app = FastAPI(title="Availability", lifespan=lifespan)
static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
settings = get_settings()
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.include_router(user_router)
app.include_router(admin_router)
