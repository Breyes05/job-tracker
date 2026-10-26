from tests.conftest import auth_headers


def make_app(client, headers=None, **overrides):
    payload = {"company": "Acme", "role": "SWE Intern", **overrides}
    response = client.post("/applications", json=payload, headers=headers)
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


# cross-user access checks
def test_list_only_returns_own_applications(client):
    alice = auth_headers(client, email="alice@example.com")
    bob = auth_headers(client, email="bob@example.com")

    make_app(client, headers=alice, company="OpenAI")
    make_app(client, headers=bob, company="Anthropic")

    alice_list = client.get("/applications", headers=alice).json()
    bob_list = client.get("/applications", headers=bob).json()

    assert [a["company"] for a in alice_list] == ["OpenAI"]
    assert [a["company"] for a in bob_list] == ["Anthropic"]


def test_cannot_get_other_users_application(client):
    alice = auth_headers(client, email="alice@example.com")
    bob = auth_headers(client, email="bob@example.com")

    alice_app = make_app(client, headers=alice, company="OpenAI")
    bad = client.get(f"/applications/{alice_app['id']}", headers=bob)

    assert bad.status_code == 404


def test_cannot_update_other_users(client):
    alice = auth_headers(client, email="alice@example.com")
    bob = auth_headers(client, email="bob@example.com")

    alice_app = make_app(client, headers=alice, company="OpenAI")
    bad = client.patch(f"/applications/{alice_app['id']}", json={"status": "offer"}, headers=bob) 
    assert bad.status_code == 404

    unchanged = client.get(f"/applications/{alice_app['id']}", headers=alice).json()
    assert unchanged["status"] == "applied"


def test_cannot_delete_other_users_application(client):
    alice = auth_headers(client, email="alice@example.com")
    bob = auth_headers(client, email="bob@example.com")
    
    alice_app = make_app(client, headers=alice, company="OpenAI")
    bad = client.delete(f"/applications/{alice_app['id']}", headers=bob)
    assert bad.status_code == 404

    unchanged = client.get(f"/applications/{alice_app['id']}", headers=alice)
    assert unchanged.status_code == 200

def test_applications_require_login(client):
    assert client.get("/applications").status_code == 401
    response = client.post("/applications", json={"company": "Acme", "role": "SWE Intern"})
    assert response.status_code == 401
    assert client.get("/applications/1").status_code == 401
    assert client.patch("/applications/1", json={"status": "offer"}).status_code == 401
    assert client.delete("/applications/1").status_code == 401