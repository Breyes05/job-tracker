def make_app(client, **overrides):
    payload = {"company": "Acme", "role": "SWE Intern", **overrides}
    response = client.post("/applications", json=payload)
    assert response.status_code == 201
    return response.json()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_application_uses_defaults(client):
    data = make_app(client)
    assert data["id"] == 1
    assert data["company"] == "Acme"
    assert data["status"] == "applied"
    assert data["date_applied"] is not None


def test_create_rejects_missing_fields(client):
    response = client.post("/applications", json={"company": "Acme"})
    assert response.status_code == 422


def test_create_rejects_invalid_status(client):
    response = client.post(
        "/applications", json={"company": "Acme", "role": "SWE", "status": "ghosted"}
    )
    assert response.status_code == 422


def test_get_application(client):
    created = make_app(client)
    response = client.get(f"/applications/{created['id']}")
    assert response.status_code == 200
    assert response.json()["role"] == "SWE Intern"


def test_get_missing_application_returns_404(client):
    assert client.get("/applications/999").status_code == 404


def test_list_filters_by_status(client):
    make_app(client, company="A", status="applied")
    make_app(client, company="B", status="interviewing")
    make_app(client, company="C", status="interviewing")

    response = client.get("/applications", params={"status": "interviewing"})
    companies = {a["company"] for a in response.json()}
    assert companies == {"B", "C"}


def test_list_filters_by_company_case_insensitive(client):
    make_app(client, company="Google")
    make_app(client, company="Meta")
    response = client.get("/applications", params={"company": "goo"})
    assert [a["company"] for a in response.json()] == ["Google"]


def test_list_sorts_by_date(client):
    make_app(client, company="Old", date_applied="2026-01-01")
    make_app(client, company="New", date_applied="2026-06-01")

    desc = client.get("/applications").json()
    assert [a["company"] for a in desc] == ["New", "Old"]

    asc = client.get("/applications", params={"order": "asc"}).json()
    assert [a["company"] for a in asc] == ["Old", "New"]


def test_patch_updates_only_sent_fields(client):
    created = make_app(client, notes="Referral from Sam")
    response = client.patch(f"/applications/{created['id']}", json={"status": "offer"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "offer"
    assert data["notes"] == "Referral from Sam"


def test_delete_application(client):
    created = make_app(client)
    assert client.delete(f"/applications/{created['id']}").status_code == 204
    assert client.get(f"/applications/{created['id']}").status_code == 404


def test_delete_missing_application_returns_404(client):
    assert client.delete("/applications/999").status_code == 404


def test_job_url_is_validated_and_stored(client):
    data = make_app(client, job_url="https://careers.acme.com/jobs/123")
    assert data["job_url"] == "https://careers.acme.com/jobs/123"

    bad = client.post(
        "/applications", json={"company": "Acme", "role": "SWE", "job_url": "not a url"}
    )
    assert bad.status_code == 422
