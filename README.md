# Job Application Tracker

[![CI](https://github.com/Breyes05/job-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/Breyes05/job-tracker/actions/workflows/ci.yml)

A REST API for tracking job applications: where you applied, what stage you're at, and how your search is going.

Built with **Python, FastAPI, SQLAlchemy, and SQLite**, secured with **JWT authentication**, and tested with **pytest**.

## Features
- User accounts: register, log in, and get a JWT access token
- Each user can only see and change their own applications
- Passwords are hashed with bcrypt and never stored or returned in plain text
- Create, view, update, and delete job applications
- Track status: `applied` → `interviewing` → `offer` / `rejected`
- Filter by status or company name, sort by date or company, paginate results
- Input validation (required fields, valid emails and URLs, valid statuses) with clear error messages
- Interactive API docs generated automatically at `/docs`

## Quick start
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create a .env file with your own secret key for signing tokens
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"   # paste the output into .env as SECRET_KEY

uvicorn app.main:app --reload --env-file .env
```
Then open http://127.0.0.1:8000/docs to try the API in your browser.

Without a `.env` file, the app falls back to a development-only key. Always set a real `SECRET_KEY` in production.

### Or run with Docker
```bash
docker build -t job-tracker .
docker run -p 8000:8000 -e SECRET_KEY=<your-secret-key> job-tracker
```

## Using the API
1. Create an account with `POST /auth/register` (`{"email": "...", "password": "..."}`, password at least 8 characters).
2. Click **Authorize** at the top of `/docs` and log in. Enter your email in the **username** field (that's the field name the OAuth2 standard uses).
3. All `/applications` endpoints now send your token automatically. Tokens expire after 30 minutes; log in again to get a new one.

Outside `/docs`, log in with `POST /auth/login` (form fields `username` and `password`) and send the returned token on each request:
```
Authorization: Bearer <access_token>
```

## Running tests
```bash
pytest
```
The 28 tests cover the endpoints, registration and login, invalid and missing tokens, and cross-user isolation (one user can't read, edit, or delete another user's applications).

Tests also run automatically on every push and pull request via GitHub Actions, which then builds the Docker image and checks that the container starts and responds on `/health`.

## API overview
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | | Create an account |
| `POST` | `/auth/login` | | Log in and get an access token |
| `GET` | `/auth/me` | ✅ | Get the logged-in user |
| `POST` | `/applications` | ✅ | Create an application |
| `GET` | `/applications` | ✅ | List your applications (`?status=`, `?company=`, `?sort_by=`, `?order=`, `?limit=`, `?offset=`) |
| `GET` | `/applications/{id}` | ✅ | Get one of your applications |
| `PATCH` | `/applications/{id}` | ✅ | Update some fields of an application |
| `DELETE` | `/applications/{id}` | ✅ | Delete an application |
| `GET` | `/health` | | Health check |

Requests without a valid token get `401`. Requests for another user's application get `404`.

## Project structure
```
app/
  main.py               # creates the FastAPI app and registers routes
  database.py           # database connection and per-request sessions
  models.py             # database tables (SQLAlchemy)
  schemas.py            # request/response validation (Pydantic)
  auth.py               # password hashing, JWT creation, current-user lookup
  routers/
    applications.py     # the /applications endpoints
    auth.py             # the /auth endpoints (register, login, me)
tests/
  conftest.py           # fresh in-memory database per test, plus login helpers
  test_applications.py  # application endpoint and cross-user isolation tests
  test_auth.py          # registration, login, and token tests
```

## Roadmap
- [x] Core CRUD API with filtering, sorting, pagination
- [x] Automated tests
- [x] User accounts with JWT authentication
- [x] Docker + GitHub Actions CI
- [ ] PostgreSQL + Alembic migrations
- [ ] Cloud deployment
- [ ] Stats endpoint (response rate, applications per week)

See [DECISIONS.md](DECISIONS.md) for the reasoning behind the technical choices.
