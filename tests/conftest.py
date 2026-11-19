"""Test setup: every test gets a fresh, empty database.

By default that's an in-memory SQLite database, so `pytest` needs no setup.
Set TEST_DATABASE_URL to run the same tests against Postgres, the database
production uses (CI does both).
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.rate_limit import failed_logins_by_email, login_attempts_by_ip

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


def make_test_engine():
    if TEST_DATABASE_URL:
        # Every test drops all tables when it finishes, so refuse to run against
        # anything that isn't clearly a throwaway test database.
        database = make_url(TEST_DATABASE_URL).database or ""
        if not database.endswith("_test"):
            raise RuntimeError(
                f"TEST_DATABASE_URL points at '{database}'. Tests drop every table, "
                "so the database name must end in '_test'."
            )
        return create_engine(TEST_DATABASE_URL)

    # StaticPool keeps one shared connection so the in-memory DB persists
    # across requests within a single test.
    return create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)


@pytest.fixture
def client():
    engine = make_test_engine()
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
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def auth_headers(client, email="user@example.com", password="password123"):
    client.post("/auth/register", json={"email":email, "password":password})
    response = client.post("/auth/login", data={"username":email, "password":password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_client(client):
    client.headers.update(auth_headers(client))
    return client
