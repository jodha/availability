from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import sessionmaker

from app.auth.passwords import verify_password
from app.models import Base, User, build_engine
from app.services.password_reset_service import (
    create_reset_token,
    find_valid_token,
    reset_user_password,
    token_is_valid,
)


@pytest.fixture
def db_session():
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    user = User(email="alex@example.com", password_hash="old", display_name="Alex")
    session.add(user)
    session.commit()
    yield session
    session.close()


def test_create_reset_token_returns_url_safe_value(db_session):
    user = db_session.query(User).first()
    token = create_reset_token(db_session, user.id)
    assert token
    assert find_valid_token(db_session, token) is not None


def test_expired_token_is_rejected(db_session):
    user = db_session.query(User).first()
    token = create_reset_token(db_session, user.id, expires_in=timedelta(hours=-1))
    assert find_valid_token(db_session, token) is None


def test_reset_user_password_updates_hash(db_session):
    user = db_session.query(User).first()
    token = create_reset_token(db_session, user.id)
    reset_user_password(db_session, token, "new-password-123")
    db_session.refresh(user)
    assert verify_password("new-password-123", user.password_hash)
    assert find_valid_token(db_session, token) is None


def test_token_is_valid_checks_expiry():
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    assert token_is_valid(future) is True
    assert token_is_valid(past) is False
