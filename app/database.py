"""Database connection setup.

SQLite stores everything in a single file (job_tracker.db), so there's nothing
to install. Swapping to Postgres later only requires changing DATABASE_URL.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./job_tracker.db")

# check_same_thread is a SQLite-only setting; FastAPI may use the connection
# from different threads, so we turn the check off.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Parent class for all database models."""


def get_db():
    """Give each request its own database session, and always close it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
