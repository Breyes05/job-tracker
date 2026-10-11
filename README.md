# Job Application Tracker

[![CI](https://github.com/BrendanReyes/job-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/BrendanReyes/job-tracker/actions/workflows/ci.yml)

A REST API for tracking job applications: where you applied, what stage you're at, and how your search is going.

Built with **Python, FastAPI, SQLAlchemy, and SQLite**, tested with **pytest**.

## Features
- Create, view, update, and delete job applications
- Track status: `applied` → `interviewing` → `offer` / `rejected`
- Filter by status or company name, sort by date or company, paginate results
- Input validation (required fields, valid URLs, valid statuses) with clear error messages
- Interactive API docs generated automatically at `/docs`

## Quick start
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Then open http://127.0.0.1:8000/docs to try the API in your browser.

### Or run with Docker
```bash
docker build -t job-tracker .
docker run -p 8000:8000 job-tracker
```

## Running tests
```bash
pytest
```
Tests also run automatically on every push and pull request via GitHub Actions, which then builds the Docker image and checks that the container starts and responds on `/health`.

## API overview
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/applications` | Create an application |
| `GET` | `/applications` | List applications (`?status=`, `?company=`, `?sort_by=`, `?order=`, `?limit=`, `?offset=`) |
| `GET` | `/applications/{id}` | Get one application |
| `PATCH` | `/applications/{id}` | Update some fields of an application |
| `DELETE` | `/applications/{id}` | Delete an application |
| `GET` | `/health` | Health check |

## Project structure
```
app/
  main.py               # creates the FastAPI app and registers routes
  database.py           # database connection and per-request sessions
  models.py             # database tables (SQLAlchemy)
  schemas.py            # request/response validation (Pydantic)
  routers/
    applications.py     # the /applications endpoints
tests/
  conftest.py           # gives each test a fresh in-memory database
  test_applications.py  # endpoint tests
```

## Roadmap
- [x] Core CRUD API with filtering, sorting, pagination
- [x] Automated tests
- [ ] User accounts with JWT authentication
- [x] Docker + GitHub Actions CI
- [ ] PostgreSQL + Alembic migrations
- [ ] Cloud deployment
- [ ] Stats endpoint (response rate, applications per week)

See [DECISIONS.md](DECISIONS.md) for the reasoning behind the technical choices.
