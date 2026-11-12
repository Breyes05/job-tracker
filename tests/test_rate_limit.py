from app.rate_limit import RateLimiter
from tests.conftest import auth_headers


class FakeClock:
    """A clock the test can move forward, so window expiry doesn't need real waiting."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def login(client, email, password, ip=None):
    headers = {"X-Forwarded-For": ip} if ip else None
    return client.post("/auth/login", data={"username": email, "password": password}, headers=headers)


# The limiter on its own

def test_limiter_blocks_after_max_attempts_and_reports_wait():
    clock = FakeClock()
    limiter = RateLimiter(max_attempts=3, window_seconds=60, clock=clock)
    for _ in range(3):
        limiter.hit("a")
    assert limiter.retry_after("a") == 60
    assert limiter.retry_after("b") == 0


def test_limiter_window_slides():
    clock = FakeClock()
    limiter = RateLimiter(max_attempts=2, window_seconds=60, clock=clock)
    limiter.hit("a")
    clock.now += 30
    limiter.hit("a")
    assert limiter.retry_after("a") == 30  # blocked until the first attempt expires
    clock.now += 30
    assert limiter.retry_after("a") == 0  # first attempt fell out of the window


def test_limiter_reset_clears_key():
    limiter = RateLimiter(max_attempts=1, window_seconds=60, clock=FakeClock())
    limiter.hit("a")
    limiter.reset("a")
    assert limiter.retry_after("a") == 0


# Through the login endpoint

def test_login_blocked_after_five_failures(client):
    auth_headers(client, email="alice@example.com")
    for _ in range(5):
        assert login(client, "alice@example.com", "wrongpassword").status_code == 401

    # Even the right password is refused while blocked.
    response = login(client, "alice@example.com", "password123")
    assert response.status_code == 429
    assert int(response.headers["retry-after"]) > 0


def test_successful_login_resets_failures(client):
    auth_headers(client, email="alice@example.com")
    for _ in range(4):
        login(client, "alice@example.com", "wrongpassword")
    assert login(client, "alice@example.com", "password123").status_code == 200

    # The earlier failures no longer count.
    for _ in range(4):
        assert login(client, "alice@example.com", "wrongpassword").status_code == 401


def test_lockout_is_per_email(client):
    auth_headers(client, email="alice@example.com")
    auth_headers(client, email="bob@example.com")
    for _ in range(5):
        login(client, "alice@example.com", "wrongpassword")

    assert login(client, "alice@example.com", "password123").status_code == 429
    assert login(client, "bob@example.com", "password123").status_code == 200


def test_lockout_ignores_email_case(client):
    auth_headers(client, email="alice@example.com")
    for _ in range(5):
        login(client, "Alice@Example.com", "wrongpassword")
    assert login(client, "alice@example.com", "password123").status_code == 429


def test_too_many_attempts_from_one_ip(client):
    for i in range(20):
        login(client, f"user{i}@example.com", "wrongpassword", ip="203.0.113.7")

    assert login(client, "someone@example.com", "wrongpassword", ip="203.0.113.7").status_code == 429
    # A different address isn't affected.
    assert login(client, "someone@example.com", "wrongpassword", ip="198.51.100.2").status_code == 401
