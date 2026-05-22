from unittest.mock import patch

from fastapi.testclient import TestClient

from app.database import get_session_factory
from app.main import app

client = TestClient(app)


def test_forgot_password_sends_email_for_known_user():
    get_session_factory()
    client.post(
        "/signup",
        data={
            "email": "reset@example.com",
            "password": "password123",
            "display_name": "Reset User",
            "invite_code": "invite123",
        },
        follow_redirects=True,
    )
    client.post("/logout", follow_redirects=True)
    with patch("app.routers.user_routes.send_password_reset_email") as send_email:
        response = client.post(
            "/forgot-password",
            data={"email": "reset@example.com"},
            follow_redirects=False,
        )
    assert response.status_code == 303
    send_email.assert_called_once()


def test_reset_password_updates_login():
    get_session_factory()
    with patch("app.routers.user_routes.send_password_reset_email") as send_email:
        client.post(
            "/signup",
            data={
                "email": "change@example.com",
                "password": "password123",
                "display_name": "Change User",
                "invite_code": "invite123",
            },
            follow_redirects=True,
        )
        client.post("/logout", follow_redirects=True)
        client.post("/forgot-password", data={"email": "change@example.com"}, follow_redirects=True)
        reset_url = send_email.call_args[0][2]
        token = reset_url.split("token=")[1]
    response = client.post(
        "/reset-password",
        data={"token": token, "password": "new-password-456"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    login_response = client.post(
        "/login",
        data={"email": "change@example.com", "password": "new-password-456"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200
