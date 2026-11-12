"""Test setup: every test gets a fresh, empty in-memory database."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.rate_limit import failed_logins_by_email, login_attempts_by_ip


@pytest.fixture
def client():
    # StaticPool keeps one shared connection so the in-memory DB persists
    # across requests within a single test.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # Rate limits live in memory, so start every test with a clean slate.
    failed_logins_by_email.clear()
    login_attempts_by_ip.clear()
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def auth_headers(client, email="user@example.com", password="password123"):
    client.post("/auth/register", json={"email":email, "password":password})
    response = client.post("/auth/login", data={"username":email, "password":password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_client(client):
    client.headers.update(auth_headers(client))
    return client