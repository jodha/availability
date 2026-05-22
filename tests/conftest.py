import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "adminpass")
os.environ.setdefault("INVITE_CODE", "invite123")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SMTP_HOST", "smtp.gmail.com")
os.environ.setdefault("SMTP_PORT", "587")
os.environ.setdefault("SMTP_USER", "test@example.com")
os.environ.setdefault("SMTP_PASSWORD", "test")
os.environ.setdefault("SMTP_FROM", "test@example.com")
os.environ.setdefault("TIMEZONE", "America/Denver")
os.environ.setdefault("MAX_EVENTS_PER_POLL", "30")
os.environ.setdefault("APP_NAME", "Availability")
os.environ.setdefault("BASE_URL", "http://testserver")

import pytest

from app.config import get_settings


@pytest.fixture(autouse=True)
def reset_app_state():
    import app.database as database_module

    get_settings.cache_clear()
    database_module._session_factory = None
    yield
    get_settings.cache_clear()
    database_module._session_factory = None

