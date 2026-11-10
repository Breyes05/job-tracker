ALLOWED = "http://localhost:5173"
UNKNOWN = "https://evil.example.com"


def test_cors_allows_frontend_origin(client):
    response = client.get("/health", headers={"Origin": ALLOWED})
    assert response.headers["access-control-allow-origin"] == ALLOWED


def test_cors_rejects_unknown_origin(client):
    response = client.get("/health", headers={"Origin": UNKNOWN})
    assert "access-control-allow-origin" not in response.headers


def test_cors_preflight_allows_frontend_origin(client):
    response = client.options(
        "/applications",
        headers={
            "Origin": ALLOWED,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED


def test_cors_preflight_rejects_unknown_origin(client):
    response = client.options(
        "/applications",
        headers={"Origin": UNKNOWN, "Access-Control-Request-Method": "POST"},
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
