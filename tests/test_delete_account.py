from tests.conftest import auth_headers
from tests.test_applications import make_app


def delete_account(client, headers, password="password123"):
    return client.request("DELETE", "/auth/me", json={"password": password}, headers=headers)


def test_delete_account_removes_user_and_their_data(client):
    alice = auth_headers(client, email="alice@example.com")
    created = make_app(client, headers=alice)
    client.patch(f"/applications/{created['id']}", json={"status": "interviewing"}, headers=alice)

    assert delete_account(client, alice).status_code == 204

    # The old token no longer works, and the email can't log in.
    assert client.get("/auth/me", headers=alice).status_code == 401
    login = client.post("/auth/login", data={"username": "alice@example.com", "password": "password123"})
    assert login.status_code == 401


def test_email_can_register_again_after_deleting(client):
    alice = auth_headers(client, email="alice@example.com")
    delete_account(client, alice)
    response = client.post("/auth/register", json={"email": "alice@example.com", "password": "password123"})
    assert response.status_code == 201


def test_delete_account_requires_correct_password(client):
    alice = auth_headers(client, email="alice@example.com")
    assert delete_account(client, alice, password="wrongpassword").status_code == 403
    assert client.get("/auth/me", headers=alice).status_code == 200


def test_deleting_one_account_leaves_others_alone(client):
    alice = auth_headers(client, email="alice@example.com")
    bob = auth_headers(client, email="bob@example.com")
    make_app(client, headers=bob)
    delete_account(client, alice)

    assert len(client.get("/applications", headers=bob).json()) == 1


def test_delete_account_requires_login(client):
    response = client.request("DELETE", "/auth/me", json={"password": "password123"})
    assert response.status_code == 401
