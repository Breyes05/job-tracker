from tests.conftest import auth_headers

# register tests
def test_register_creates_user(client):
    response = client.post("/auth/register", json={"email": "new@example.com", "password": "password123"})
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@example.com"
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_rejects_duplicate_email(client):
    payload = {"email": "new@example.com", "password": "password123"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 409


def test_register_rejects_invalid_email(client):
    response = client.post("/auth/register", json={"email": "new", "password": "password123"})
    assert response.status_code == 422


def test_register_rejects_short_password(client):
    response = client.post("/auth/register", json={"email": "new@example.com", "password": "short"})
    assert response.status_code == 422


# login tests
def test_login_returns_token(client):
    response = client.post("/auth/register", json={"email": "new@example.com", "password": "password123"})
    assert response.status_code == 201

    response = client.post("/auth/login", data={"username": "new@example.com", "password": "password123"})
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_rejects_wrong_password(client):
    response = client.post("/auth/register", json={"email": "new@example.com", "password": "password123"})
    assert response.status_code == 201
    
    response = client.post("/auth/login", data={"username": "new@example.com", "password": "incorrectpassword"})
    assert response.status_code == 401


def test_login_rejects_unknown_email(client):
    response = client.post("/auth/login", data={"username": "new@example.com", "password": "incorrectpassword"})
    assert response.status_code == 401


# me tests
def test_me_returns_current_user(client):
    auth_headers(client, email="first@example.com")
    headers = auth_headers(client, email="me@example.com")
    response = client.get("/auth/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert "hashed_password" not in data


def test_me_requires_token(client):
    response = client.get("/auth/me", headers=None)
    assert response.status_code == 401


def test_me_rejects_invalid_token(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer garbage"})
    assert response.status_code == 401