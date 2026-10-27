# Design Decisions

Why the project is built the way it is. Each entry covers what was chosen, what else was considered, and the trade-off.

---

## 1. FastAPI as the web framework
**Chose:** FastAPI
**Alternatives:** Flask, Django
**Why:** FastAPI uses Python type hints to validate requests and generate interactive API docs (`/docs`) automatically, so there's less boilerplate. Flask is simpler but needs extra libraries for validation and docs. Django is "batteries included" (admin panel, templates, ORM), which is more than a pure API needs.
**Trade-off:** FastAPI is newer than Flask and Django, so there are fewer tutorials and plugins.

## 2. SQLite first, then PostgreSQL
**Chose:** SQLite during early development, PostgreSQL once the app was deployed
**Alternatives:** PostgreSQL from the start, MongoDB
**Why:** SQLite is a single file with nothing to install or run, so development started quickly. The data is relational (users have many applications) and fits a SQL database well, which is why MongoDB wasn't chosen.
**Trade-off:** SQLite handles many concurrent writes poorly and lives on the server's disk, which hosts like Render wipe on every deploy, so it isn't suitable for production. Because the code goes through SQLAlchemy and reads `DATABASE_URL` from the environment, the switch to Postgres needed no application code changes, just a new URL and a driver (`psycopg`). Tests still use in-memory SQLite for speed.

## 3. SQLAlchemy ORM instead of raw SQL
**Chose:** SQLAlchemy ORM
**Alternatives:** Writing SQL strings by hand
**Why:** Tables are defined as Python classes, and the ORM builds safe parameterized queries, which prevents SQL injection. The same code also works across different databases.
**Trade-off:** It adds a layer of abstraction. For complex queries, raw SQL can be clearer or faster.

## 4. Separate Pydantic schemas from database models
**Chose:** `schemas.py` (what the API accepts and returns) separate from `models.py` (what's stored)
**Why:** Clients shouldn't control fields like `id` or `created_at`, and the database stores things (like password hashes) that must never be sent back. Separate schemas make that explicit. Pydantic also rejects bad input automatically with a `422` error.
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

## 10. Docker + GitHub Actions for CI
**Chose:** A Dockerfile and a GitHub Actions workflow that runs the tests, builds the image, and starts the container to check `/health`
**Alternatives:** Running tests only locally, other CI services (CircleCI, Travis)
**Why:** Docker packages the app with its exact Python version and dependencies, so it runs the same on a laptop, in CI, and on a cloud host. CI runs the tests on every push, so a broken change shows up immediately instead of at deploy time. GitHub Actions is built into GitHub and free for public repos. The Docker image is only built after the tests pass, and the smoke test catches problems that unit tests miss, like a missing file in the image or a bad startup command.
**Trade-off:** The image runs as a non-root user and copies dependencies before code so builds are cached, which makes the Dockerfile a little longer than the minimum.

## 11. JWT for authentication
**Chose:** JSON Web Tokens (JWT), signed with HS256 and a `SECRET_KEY` read from the environment, expiring after 30 minutes
**Alternatives:** Session-based auth (a sessions table and a session ID cookie)
**Why:** A JWT carries the user's ID (`sub`) and expiration (`exp`) and is signed with a key only the server knows, so the server can verify it without storing anything or looking it up. That's what makes it stateless, and it means any server with the key can check a token. FastAPI's `OAuth2PasswordBearer` also wires it into the Authorize button in `/docs`. The token payload is readable by anyone, so it only contains the user ID and expiration, never anything sensitive.
**Trade-off:** Because nothing is stored, a token can't be revoked before it expires, even after logout or a password change. A stolen token works until then, so the expiration is kept short (30 minutes), and production should run over HTTPS. Sessions could be revoked instantly, but they need a database lookup on every request.

## 12. bcrypt for password hashing
**Chose:** bcrypt, with a random salt per password
**Alternatives:** A fast hash like SHA-256, or storing passwords as plain text
**Why:** Hashing is one-way, so a leaked database doesn't reveal passwords. bcrypt adds a random salt (stored inside the hash), so two users with the same password get different hashes and precomputed rainbow tables don't work. It's also deliberately slow, which makes guessing passwords by brute force expensive. Fast hashes like SHA-256 are built for speed, which helps attackers.
**Trade-off:** Hashing takes noticeable time, which slows down login and the test suite slightly. bcrypt also only accepts passwords up to 72 bytes, so the schema limits passwords to 72 characters to return a clean `422` instead of a server error.

## 13. 404 instead of 403 for other users' applications
**Chose:** Return `404 Not Found` when a user asks for an application that belongs to someone else
**Alternatives:** `403 Forbidden`
**Why:** A `403` confirms that the application ID exists, which leaks information about other users' data. A `404` gives the same response whether the ID doesn't exist or belongs to someone else, so other users' data is effectively invisible. This guards against IDOR (insecure direct object reference), where someone guesses IDs to reach data that isn't theirs. The ownership check lives in one helper (`get_application_or_404`), so get, update, and delete all share it, and tests check that the data really is unchanged afterward.
**Trade-off:** The error is less specific, which can make debugging a little harder for a legitimate user who mistypes an ID.

## 14. Alembic migrations instead of `create_all`
**Chose:** Alembic, with one migration file per schema change, generated with `--autogenerate` and reviewed before applying
**Alternatives:** `Base.metadata.create_all()` on startup, writing SQL scripts by hand
**Why:** `create_all` only creates missing tables; it silently ignores changes to existing ones (this came up when `user_id` was added in the auth work, and the only fix was deleting the database). With real users, deleting the database isn't an option. Alembic records each change as an `upgrade()`/`downgrade()` script in git and tracks which ones a database has applied in an `alembic_version` table, so only new changes run.
**Trade-off:** Every model change now needs a migration, and autogenerate isn't perfect: for example, it didn't drop the Postgres `status` enum type in `downgrade()`, which had to be added by hand. Generated migrations always need to be read before they're applied. Tests still build their in-memory database with `create_all`, which is fine for throwaway databases.

## 15. Neon for the database, Render for the API
**Chose:** A Neon serverless Postgres database and a Render web service built from the Dockerfile
**Alternatives:** Render's own Postgres, Supabase, Railway, Fly.io
**Why:** Render deploys straight from the Dockerfile on every merge to `main`, provides HTTPS automatically, and has a free tier. Render's free Postgres databases expire after 30 days, which would delete real users' data, so the database lives on Neon, whose free tier doesn't expire. Keeping the database separate from the app host is also common in production. The connection uses `sslmode=require`, so traffic between Render and Neon is encrypted.
**Trade-off:** Render's free tier spins the API down after about 15 minutes without traffic, so the next request takes 30 to 60 seconds. Two providers means two dashboards and two sets of settings. A paid tier would remove the cold starts if the app gets regular users.

## 16. Run migrations when the container starts
**Chose:** The Docker image runs `alembic upgrade head && uvicorn ...` on every start, and Docker Compose waits for Postgres to pass a health check before starting the API
**Alternatives:** Running migrations by hand before each deploy, a separate pre-deploy step
**Why:** Nobody has to remember to migrate. Every deploy, local or on Render, brings the database up to date before the server accepts requests, and `upgrade head` does nothing when there are no new migrations, so it's safe to run every time. The `&&` means the server doesn't start if a migration fails, so a broken schema fails loudly instead of serving errors. The port comes from `${PORT:-8000}`, so the same image works locally and on Render. CI starts the same Compose stack and registers a user, which only succeeds if the migrations ran against Postgres.
**Trade-off:** With several instances running at once, they'd all try to migrate at the same time. At one instance that doesn't matter; at scale, migrations would move to a separate deploy step.
