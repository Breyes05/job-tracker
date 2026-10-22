def make_app(client, **overrides):
    payload = {"company": "Acme", "role": "SWE Intern", **overrides}
    response = client.post("/applications", json=payload)
    assert response.status_code == 201
    return response.json()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_application_uses_defaults(auth_client):
    data = make_app(auth_client)
    assert data["id"] == 1
    assert data["company"] == "Acme"
    assert data["status"] == "applied"
    assert data["date_applied"] is not None


def test_create_rejects_missing_fields(auth_client):
    response = auth_client.post("/applications", json={"company": "Acme"})
    assert response.status_code == 422


def test_create_rejects_invalid_status(auth_client):
    response = auth_client.post(
        "/applications", json={"company": "Acme", "role": "SWE", "status": "ghosted"}
    )
    assert response.status_code == 422


def test_get_application(auth_client):
    created = make_app(auth_client)
    response = auth_client.get(f"/applications/{created['id']}")
    assert response.status_code == 200
    assert response.json()["role"] == "SWE Intern"


def test_get_missing_application_returns_404(auth_client):
    assert auth_client.get("/applications/999").status_code == 404


def test_list_filters_by_status(auth_client):
    make_app(auth_client, company="A", status="applied")
    make_app(auth_client, company="B", status="interviewing")
    make_app(auth_client, company="C", status="interviewing")

    response = auth_client.get("/applications", params={"status": "interviewing"})
    companies = {a["company"] for a in response.json()}
    assert companies == {"B", "C"}


def test_list_filters_by_company_case_insensitive(auth_client):
    make_app(auth_client, company="Google")
    make_app(auth_client, company="Meta")
    response = auth_client.get("/applications", params={"company": "goo"})
    assert [a["company"] for a in response.json()] == ["Google"]


def test_list_sorts_by_date(auth_client):
    make_app(auth_client, company="Old", date_applied="2026-01-01")
    make_app(auth_client, company="New", date_applied="2026-06-01")

    desc = auth_client.get("/applications").json()
    assert [a["company"] for a in desc] == ["New", "Old"]

    asc = auth_client.get("/applications", params={"order": "asc"}).json()
    assert [a["company"] for a in asc] == ["Old", "New"]


def test_patch_updates_only_sent_fields(auth_client):
    created = make_app(auth_client, notes="Referral from Sam")
    response = auth_client.patch(f"/applications/{created['id']}", json={"status": "offer"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "offer"
    assert data["notes"] == "Referral from Sam"


def test_delete_application(auth_client):
    created = make_app(auth_client)
    assert auth_client.delete(f"/applications/{created['id']}").status_code == 204
    assert auth_client.get(f"/applications/{created['id']}").status_code == 404


def test_delete_missing_application_returns_404(auth_client):
    assert auth_client.delete("/applications/999").status_code == 404


def test_job_url_is_validated_and_stored(auth_client):
    data = make_app(auth_client, job_url="https://careers.acme.com/jobs/123")
    assert data["job_url"] == "https://careers.acme.com/jobs/123"

    bad = auth_client.post(
        "/applications", json={"company": "Acme", "role": "SWE", "job_url": "not a url"}
    )
    assert bad.status_code == 422
