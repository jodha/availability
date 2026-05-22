from fastapi.testclient import TestClient

from app.database import get_session_factory
from app.main import app

client = TestClient(app)


def test_signup_requires_valid_invite_code():
    get_session_factory()
    response = client.post(
        "/signup",
        data={
            "email": "bad@example.com",
            "password": "password123",
            "display_name": "Bad User",
            "invite_code": "wrong-code",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "Invalid" in response.headers["location"]


def test_signup_and_login_flow():
    get_session_factory()
    client.post(
        "/signup",
        data={
            "email": "alex@example.com",
            "password": "password123",
            "display_name": "Alex",
            "invite_code": "invite123",
        },
        follow_redirects=True,
    )
    client.post("/logout", follow_redirects=True)
    response = client.post(
        "/login",
        data={"email": "alex@example.com", "password": "password123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "No active poll" in response.text or "Poll" in response.text
