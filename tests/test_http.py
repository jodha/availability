from fastapi.testclient import TestClient

from app.database import get_session_factory
from app.main import app
from app.services.allowed_email_service import add_allowed_email

client = TestClient(app)


def test_login_rejects_unlisted_email():
    get_session_factory()
    response = client.post(
        "/login",
        data={"email": "unknown@example.com"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "not%20authorized" in response.headers["location"] or "authorized" in response.headers["location"]


def test_login_and_display_name_flow():
    db = get_session_factory()()
    add_allowed_email(db, "alex@example.com")
    db.close()
    client.post("/login", data={"email": "alex@example.com"}, follow_redirects=True)
    response = client.post(
        "/set-display-name",
        data={"display_name": "Alex"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    client.post("/logout", follow_redirects=True)
    response = client.post("/login", data={"email": "alex@example.com"}, follow_redirects=True)
    assert response.status_code == 200
    assert "Poll" in response.text or "poll" in response.text.lower()
