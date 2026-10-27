# Job Application Tracker

[![CI](https://github.com/Breyes05/job-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/Breyes05/job-tracker/actions/workflows/ci.yml)

A REST API for tracking job applications: where you applied, what stage you're at, and how your search is going.

**Live API:** https://job-tracker-t7rk.onrender.com/docs (hosted on Render's free tier, so the first request after a quiet period can take 30 to 60 seconds while it wakes up)

Built with **Python, FastAPI, SQLAlchemy, and PostgreSQL**, secured with **JWT authentication**, migrated with **Alembic**, and tested with **pytest**.

## Features
- User accounts: register, log in, and get a JWT access token
- Each user can only see and change their own applications
- Passwords are hashed with bcrypt and never stored or returned in plain text
- Create, view, update, and delete job applications
- Track status: `applied` → `interviewing` → `offer` / `rejected`
- Filter by status or company name, sort by date or company, paginate results
- Input validation (required fields, valid emails and URLs, valid statuses) with clear error messages
- Interactive API docs generated automatically at `/docs`

## Quick start (Docker Compose)
The fastest way to run everything (Postgres and the API) is one command:
```bash
docker compose up --build
```
Then open http://localhost:8000/docs. The API waits for Postgres to be ready, applies any database migrations, and then starts.

## Local development
To run the API directly on your machine (with auto-reload), start only the database in Docker:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create a .env file and put your own secret key in it
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"   # paste the output into .env as SECRET_KEY

docker compose up -d db                 # start Postgres
set -a; source .env; set +a             # load .env into this terminal (Alembic doesn't read it)
alembic upgrade head                    # create the tables
uvicorn app.main:app --reload --env-file .env
```
Then open http://127.0.0.1:8000/docs.

Without a `SECRET_KEY`, the app falls back to a development-only key. Production always sets a real one.

## Database migrations
The database schema is managed with Alembic. `create_all` can create tables but can't change existing ones, so every schema change is a migration file in `migrations/versions/`, committed to git like code.

After changing a model in `app/models.py`:
```bash
alembic revision --autogenerate -m "Describe the change"   # writes a new migration
# open the new file in migrations/versions/ and check it before applying
alembic upgrade head                                       # apply it
```
`alembic downgrade -1` undoes the most recent migration. The Docker image runs `alembic upgrade head` on every start, so deployed databases pick up new migrations automatically.

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
The 28 tests cover the endpoints, registration and login, invalid and missing tokens, and cross-user isolation (one user can't read, edit, or delete another user's applications). They run against a fresh in-memory SQLite database, so they don't need Postgres.

GitHub Actions runs the tests on every push to `main` and every pull request. If they pass, it starts the full Docker Compose stack (Postgres and the API), checks `/health`, and registers a user, which only succeeds if the migrations ran against Postgres.

## Deployment
Every merge to `main` deploys automatically:
```
push → GitHub Actions (tests + Postgres smoke test) → merge to main → Render builds the Docker image
                                                               → alembic upgrade head → Neon Postgres
```
- **API:** [Render](https://render.com) web service, built from the `Dockerfile`, with the health check path set to `/health`
- **Database:** [Neon](https://neon.tech) serverless Postgres
- **Configuration:** `DATABASE_URL` (the Neon connection string, starting with `postgresql+psycopg://`) and `SECRET_KEY` are set as environment variables in Render's dashboard and are never committed

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
migrations/
  env.py                # connects Alembic to DATABASE_URL and the app's models
  versions/             # one file per schema change
tests/
  conftest.py           # fresh in-memory database per test, plus login helpers
  test_applications.py  # application endpoint and cross-user isolation tests
  test_auth.py          # registration, login, and token tests
alembic.ini             # Alembic configuration
docker-compose.yml      # local Postgres + API
Dockerfile              # production image (runs migrations, then the server)
```

## Roadmap
- [x] Core CRUD API with filtering, sorting, pagination
- [x] Automated tests
- [x] User accounts with JWT authentication
- [x] Docker + GitHub Actions CI
- [x] PostgreSQL + Alembic migrations
- [x] Cloud deployment
- [ ] React frontend
- [ ] Stats endpoint (response rate, applications per week)

See [DECISIONS.md](DECISIONS.md) for the reasoning behind the technical choices.
