from datetime import date, timedelta

from app.routers import applications as applications_router
from tests.conftest import auth_headers
from tests.test_applications import make_app


def days_ago(days):
    return (date.today() - timedelta(days=days)).isoformat()


def follow_up_companies(client, headers=None):
    response = client.get("/applications/follow-ups", headers=headers)
    assert response.status_code == 200
    return [a["company"] for a in response.json()]


def test_old_applications_still_in_applied_need_a_follow_up(auth_client):
    make_app(auth_client, company="Old", date_applied=days_ago(20))
    make_app(auth_client, company="Older", date_applied=days_ago(30))
    make_app(auth_client, company="Recent", date_applied=days_ago(3))
    make_app(auth_client, company="Moved on", status="interviewing", date_applied=days_ago(30))

    assert follow_up_companies(auth_client) == ["Older", "Old"]  # oldest first


def test_marking_followed_up_hides_it_for_two_weeks(auth_client, monkeypatch):
    created = make_app(auth_client, company="Acme", date_applied=days_ago(20))
    response = auth_client.post(f"/applications/{created['id']}/follow-up")
    assert response.status_code == 200
    assert response.json()["followed_up_at"] is not None
    assert follow_up_companies(auth_client) == []

    # Fifteen days later with still no reply, it comes back.
    later = applications_router.utcnow() + timedelta(days=15)
    monkeypatch.setattr(applications_router, "utcnow", lambda: later)
    assert follow_up_companies(auth_client) == ["Acme"]


def test_moving_out_of_applied_removes_the_reminder(auth_client):
    created = make_app(auth_client, company="Acme", date_applied=days_ago(20))
    auth_client.patch(f"/applications/{created['id']}", json={"status": "rejected"})
    assert follow_up_companies(auth_client) == []


def test_follow_ups_only_include_your_applications(client):
    alice = auth_headers(client, email="alice@example.com")
    bob = auth_headers(client, email="bob@example.com")
    created = make_app(client, headers=alice, date_applied=days_ago(20))

    assert follow_up_companies(client, headers=bob) == []
    assert client.post(f"/applications/{created['id']}/follow-up", headers=bob).status_code == 404


def test_follow_ups_require_login(client):
    assert client.get("/applications/follow-ups").status_code == 401
    assert client.post("/applications/1/follow-up").status_code == 401
