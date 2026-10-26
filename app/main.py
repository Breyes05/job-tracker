"""App entry point. Run with: uvicorn app.main:app --reload"""

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import applications, auth

# Create tables on startup. Fine for now; we'll switch to Alembic migrations
# in a later phase so schema changes don't require wiping the database.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Job Application Tracker",
    description="Track your job applications, their status, and your progress.",
    version="0.1.0",
)

app.include_router(applications.router)
app.include_router(auth.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
