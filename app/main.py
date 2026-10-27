"""App entry point. Run with: uvicorn app.main:app --reload"""

from fastapi import FastAPI

from app.routers import applications, auth


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
