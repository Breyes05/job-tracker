"""App entry point. Run with: uvicorn app.main:app --reload"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import applications, auth

# Frontends allowed to call this API from a browser. Defaults to the local
# Vite dev server; production sets CORS_ORIGINS to the deployed frontend's URL.
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

app = FastAPI(
    title="Job Application Tracker",
    description="Track your job applications, their status, and your progress.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(applications.router)
app.include_router(auth.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
