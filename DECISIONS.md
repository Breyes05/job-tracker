# Design Decisions

Why the project is built the way it is. Each entry covers what was chosen, what else was considered, and the trade-off.

---

## 1. FastAPI as the web framework
**Chose:** FastAPI
**Alternatives:** Flask, Django
**Why:** FastAPI uses Python type hints to validate requests and generate interactive API docs (`/docs`) automatically, so there's less boilerplate. Flask is simpler but needs extra libraries for validation and docs. Django is "batteries included" (admin panel, templates, ORM), which is more than a pure API needs.
**Trade-off:** FastAPI is newer than Flask and Django, so there are fewer tutorials and plugins.

## 2. SQLite for now, PostgreSQL later
**Chose:** SQLite during development
**Alternatives:** PostgreSQL from the start, MongoDB
**Why:** SQLite is a single file with nothing to install or run, so development starts quickly. The data is relational (users have many applications) and fits a SQL database well, which is why MongoDB wasn't chosen.
**Trade-off:** SQLite handles many concurrent writes poorly, so it isn't suitable for production with many users. Because the code goes through SQLAlchemy, switching to Postgres means changing one setting (`DATABASE_URL`).

## 3. SQLAlchemy ORM instead of raw SQL
**Chose:** SQLAlchemy ORM
**Alternatives:** Writing SQL strings by hand
**Why:** Tables are defined as Python classes, and the ORM builds safe parameterized queries, which prevents SQL injection. The same code also works across different databases.
**Trade-off:** It adds a layer of abstraction. For complex queries, raw SQL can be clearer or faster.

## 4. Separate Pydantic schemas from database models
**Chose:** `schemas.py` (what the API accepts and returns) separate from `models.py` (what's stored)
**Why:** Clients shouldn't control fields like `id` or `created_at`, and later on we'll store things (like password hashes) that must never be sent back. Separate schemas make that explicit. Pydantic also rejects bad input automatically with a `422` error.
**Trade-off:** Some fields are defined twice.

## 5. PATCH instead of PUT for updates
**Chose:** `PATCH /applications/{id}`
**Why:** PUT means "replace the whole object," so the client would have to resend every field just to change the status. PATCH means "change only these fields," which matches how the app is actually used (for example, moving an application from `applied` to `interviewing`). `exclude_unset=True` makes sure only the fields the client sent get updated.

## 6. Status as a fixed set of values (Enum)
**Chose:** `applied | interviewing | offer | rejected`
**Alternatives:** Free-text string
**Why:** Free text leads to messy data ("Interviewing", "interview", "intrvw") that breaks filtering and stats. An Enum makes invalid values impossible and the API rejects them.
**Trade-off:** Adding a new stage requires a code change.

## 7. Pagination with limit/offset
**Chose:** `?limit=50&offset=0` (max 200)
**Alternatives:** No pagination, cursor-based pagination
**Why:** Returning every row gets slow as data grows. Limit/offset is simple and good enough at this scale.
**Trade-off:** Offset gets slower on very large tables, and results can shift if rows are added between pages. Cursor-based pagination fixes both but is more complex.

## 8. Fresh in-memory database for each test
**Chose:** pytest fixture that creates an in-memory SQLite database per test and swaps it in using FastAPI's dependency overrides
**Why:** Tests never touch real data, don't affect each other, and run in milliseconds. Swapping the database through `get_db` is the payoff of using dependency injection.

## 9. Indexes on `company` and `status`
**Why:** Those are the columns we filter on. An index lets the database find matching rows without scanning the whole table.
**Trade-off:** Indexes make writes slightly slower and take extra storage.
