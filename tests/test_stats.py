from datetime import date, datetime, timedelta

from app.routers import applications as applications_router
from tests.conftest import auth_headers
from tests.test_applications import make_app


class Clock:
    """Controls the time status changes are recorded at, so tests can space them out."""

    def __init__(self, monkeypatch, start):
        self.now = start
        monkeypatch.setattr(applications_router, "utcnow", lambda: self.now)

    def advance(self, days=0, minutes=0):
        self.now += timedelta(days=days, minutes=minutes)


def move(client, application_id, status, headers=None):
    response = client.patch(f"/applications/{application_id}", json={"status": status}, headers=headers)
    assert response.status_code == 200


def stats(client, headers=None):
    response = client.get("/stats", headers=headers)
    assert response.status_code == 200
    return response.json()


def test_stats_with_no_applications(auth_client):
    data = stats(auth_client)
    assert data["total"] == 0
    assert data["response_rate"] is None
    assert data["median_days_to_response"] is None
    assert len(data["weekly"]) == 8
    assert all(week["count"] == 0 for week in data["weekly"])


def test_counts_and_rates(auth_client, monkeypatch):
    clock = Clock(monkeypatch, datetime(2026, 11, 2, 12, 0))
    waiting = make_app(auth_client, company="Waiting")
    interview = make_app(auth_client, company="Interview")
    rejected = make_app(auth_client, company="Rejected")
    offer = make_app(auth_client, company="Offer")
    del waiting  # never hears back

    clock.advance(days=3)
    move(auth_client, interview["id"], "interviewing")
    move(auth_client, rejected["id"], "rejected")
    move(auth_client, offer["id"], "interviewing")
    clock.advance(days=7)
    move(auth_client, offer["id"], "offer")

    data = stats(auth_client)
    assert (data["total"], data["responded"], data["interviewed"], data["offers"], data["rejected"]) == (4, 3, 2, 1, 1)
    assert data["response_rate"] == 0.75
    assert data["interview_rate"] == 0.5
    assert data["offer_rate"] == 0.25


def test_moving_back_does_not_erase_progress(auth_client, monkeypatch):
    clock = Clock(monkeypatch, datetime(2026, 11, 2, 12, 0))
    created = make_app(auth_client)
    move(auth_client, created["id"], "interviewing")
    clock.advance(days=2)  # well past the correction window
    move(auth_client, created["id"], "applied")

    data = stats(auth_client)
    assert data["interviewed"] == 1
    assert data["response_rate"] == 1.0


def test_quick_undo_does_not_count(auth_client):
    created = make_app(auth_client)
    move(auth_client, created["id"], "interviewing")
    move(auth_client, created["id"], "applied")  # corrected within the window

    assert stats(auth_client)["responded"] == 0


def test_median_days_to_first_response(auth_client, monkeypatch):
    clock = Clock(monkeypatch, datetime(2026, 11, 20, 12, 0))
    replied_in = {"A": 2, "B": 5, "C": 30}
    for company, days in replied_in.items():
        applied_on = (clock.now - timedelta(days=days)).date().isoformat()
        created = make_app(auth_client, company=company, date_applied=applied_on)
        move(auth_client, created["id"], "interviewing")

    assert stats(auth_client)["median_days_to_response"] == 5


def test_added_after_hearing_back_has_no_response_time(auth_client):
    # Created straight into Interviewing: we don't know when the company replied.
    make_app(auth_client, status="interviewing")
    data = stats(auth_client)
    assert data["responded"] == 1
    assert data["median_days_to_response"] is None


def test_applications_per_week(auth_client):
    today = date.today()
    this_monday = today - timedelta(days=today.weekday())
    make_app(auth_client, date_applied=today.isoformat())
    make_app(auth_client, date_applied=today.isoformat())
    make_app(auth_client, date_applied=(this_monday - timedelta(weeks=2)).isoformat())
    make_app(auth_client, date_applied=(this_monday - timedelta(weeks=20)).isoformat())  # too old to show

    weekly = stats(auth_client)["weekly"]
    assert weekly[-1] == {"week_start": this_monday.isoformat(), "count": 2}
    assert weekly[-3]["count"] == 1
    assert sum(week["count"] for week in weekly) == 3


def test_stats_only_include_your_applications(client):
    alice = auth_headers(client, email="alice@example.com")
    bob = auth_headers(client, email="bob@example.com")
    created = make_app(client, headers=alice)
    move(client, created["id"], "offer", headers=alice)
    make_app(client, headers=bob)

    data = stats(client, headers=bob)
    assert (data["total"], data["responded"], data["offers"]) == (1, 0, 0)


def test_stats_require_login(client):
    assert client.get("/stats").status_code == 401
