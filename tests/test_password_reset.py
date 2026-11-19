import re
from datetime import timedelta

import pytest

from app.routers import auth as auth_router
from tests.conftest import auth_headers


@pytest.fixture
def outbox(monkeypatch):
    """Capture emails instead of sending them."""
    sent = []
    monkeypatch.setattr(auth_router, "send_email", lambda to, subject, body: sent.append({"to": to, "body": body}))
    return sent


def request_reset(client, email):
    return client.post("/auth/forgot-password", json={"email": email})


def token_from(email_message):
    return re.search(r"token=([\w-]+)", email_message["body"]).group(1)


def reset(client, token, password="newpassword123"):
    return client.post("/auth/reset-password", json={"token": token, "password": password})


def login(client, email, password):
    return client.post("/auth/login", data={"username": email, "password": password})


def test_full_reset_flow(client, outbox):
    auth_headers(client, email="alice@example.com")
    response = request_reset(client, "alice@example.com")
    assert response.status_code == 202
    assert len(outbox) == 1 and outbox[0]["to"] == "alice@example.com"
    assert "/reset-password?token=" in outbox[0]["body"]

    assert reset(client, token_from(outbox[0])).status_code == 200
    assert login(client, "alice@example.com", "newpassword123").status_code == 200
    assert login(client, "alice@example.com", "password123").status_code == 401


def test_unknown_email_gets_the_same_response_and_no_email(client, outbox):
    auth_headers(client, email="alice@example.com")
    known = request_reset(client, "alice@example.com")
    unknown = request_reset(client, "nobody@example.com")
    assert (known.status_code, known.json()) == (unknown.status_code, unknown.json())
    assert [m["to"] for m in outbox] == ["alice@example.com"]


def test_reset_link_works_only_once(client, outbox):
    auth_headers(client, email="alice@example.com")
    request_reset(client, "alice@example.com")
    token = token_from(outbox[0])
    assert reset(client, token).status_code == 200
    assert reset(client, token, password="anotherpassword").status_code == 400


def test_only_the_newest_link_works(client, outbox):
    auth_headers(client, email="alice@example.com")
    request_reset(client, "alice@example.com")
    request_reset(client, "alice@example.com")
    first, second = token_from(outbox[0]), token_from(outbox[1])
    assert reset(client, first).status_code == 400
    assert reset(client, second).status_code == 200


def test_expired_link_is_rejected(client, outbox, monkeypatch):
    auth_headers(client, email="alice@example.com")
    request_reset(client, "alice@example.com")
    later = auth_router.utcnow() + timedelta(hours=2)
    monkeypatch.setattr(auth_router, "utcnow", lambda: later)
    assert reset(client, token_from(outbox[0])).status_code == 400


def test_made_up_token_is_rejected(client):
    assert reset(client, "not-a-real-token").status_code == 400


def test_reset_logs_out_existing_sessions(client, outbox, monkeypatch):
    old_session = auth_headers(client, email="alice@example.com")
    request_reset(client, "alice@example.com")
    # Reset a little later than the old token was issued.
    later = auth_router.utcnow() + timedelta(seconds=5)
    monkeypatch.setattr(auth_router, "utcnow", lambda: later)
    reset(client, token_from(outbox[0]))

    assert client.get("/auth/me", headers=old_session).status_code == 401


def test_new_password_must_be_long_enough(client, outbox):
    auth_headers(client, email="alice@example.com")
    request_reset(client, "alice@example.com")
    assert reset(client, token_from(outbox[0]), password="short").status_code == 422


def test_reset_requests_are_rate_limited(client, outbox):
    auth_headers(client, email="alice@example.com")
    for _ in range(3):
        assert request_reset(client, "alice@example.com").status_code == 202
    assert request_reset(client, "alice@example.com").status_code == 429
    assert len(outbox) == 3
