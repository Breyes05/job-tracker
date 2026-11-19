from datetime import timedelta

from app.routers import applications as applications_router
from tests.conftest import auth_headers
from tests.test_applications import make_app


def history(client, application_id, headers=None):
    response = client.get(f"/applications/{application_id}/history", headers=headers)
    assert response.status_code == 200
    return [(e["from_status"], e["to_status"]) for e in response.json()]


def set_status(client, application_id, status):
    response = client.patch(f"/applications/{application_id}", json={"status": status})
    assert response.status_code == 200


def advance_clock(monkeypatch, minutes):
    """Pretend `minutes` have passed, so the correction window can expire without waiting."""
    real_now = applications_router.utcnow()
    monkeypatch.setattr(applications_router, "utcnow", lambda: real_now + timedelta(minutes=minutes))


def test_creating_an_application_records_its_starting_status(auth_client):
    created = make_app(auth_client, status="interviewing")
    assert history(auth_client, created["id"]) == [(None, "interviewing")]


def test_changing_status_adds_an_event(auth_client):
    created = make_app(auth_client)
    set_status(auth_client, created["id"], "interviewing")
    assert history(auth_client, created["id"]) == [(None, "applied"), ("applied", "interviewing")]


def test_editing_other_fields_adds_no_event(auth_client):
    created = make_app(auth_client)
    auth_client.patch(f"/applications/{created['id']}", json={"notes": "Recruiter is Alex"})
    set_status(auth_client, created["id"], "applied")  # same status as before
    assert history(auth_client, created["id"]) == [(None, "applied")]


def test_quick_undo_is_treated_as_a_correction(auth_client):
    created = make_app(auth_client)
    set_status(auth_client, created["id"], "interviewing")
    set_status(auth_client, created["id"], "applied")  # misclick fixed right away
    assert history(auth_client, created["id"]) == [(None, "applied")]


def test_moving_back_after_the_window_is_kept_as_history(auth_client, monkeypatch):
    created = make_app(auth_client)
    set_status(auth_client, created["id"], "interviewing")
    advance_clock(monkeypatch, minutes=10)
    set_status(auth_client, created["id"], "applied")
    assert history(auth_client, created["id"]) == [
        (None, "applied"),
        ("applied", "interviewing"),
        ("interviewing", "applied"),
    ]


def test_a_different_quick_change_is_not_an_undo(auth_client):
    created = make_app(auth_client)
    set_status(auth_client, created["id"], "interviewing")
    set_status(auth_client, created["id"], "offer")  # moving forward again, not reverting
    assert history(auth_client, created["id"]) == [
        (None, "applied"),
        ("applied", "interviewing"),
        ("interviewing", "offer"),
    ]


def test_deleting_an_application_deletes_its_history(auth_client):
    created = make_app(auth_client)
    set_status(auth_client, created["id"], "interviewing")
    assert auth_client.delete(f"/applications/{created['id']}").status_code == 204
    assert auth_client.get(f"/applications/{created['id']}/history").status_code == 404


def test_cannot_see_another_users_history(client):
    alice = auth_headers(client, email="alice@example.com")
    bob = auth_headers(client, email="bob@example.com")
    created = make_app(client, headers=alice)
    assert client.get(f"/applications/{created['id']}/history", headers=bob).status_code == 404


def test_history_requires_login(client):
    assert client.get("/applications/1/history").status_code == 401
