"""Database tables, defined as Python classes (SQLAlchemy ORM)."""

import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, String, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Status(str, enum.Enum):
    """The stages a job application moves through."""

    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFER = "offer"
    REJECTED = "rejected"


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str] = mapped_column(String(200), index=True)
    role: Mapped[str] = mapped_column(String(200))
    status: Mapped[Status] = mapped_column(Enum(Status), default=Status.APPLIED, index=True)
    date_applied: Mapped[date] = mapped_column(Date, default=date.today)
    job_url: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    # When the user last marked this application as followed up (UTC), if ever.
    followed_up_at: Mapped[datetime | None] = mapped_column(DateTime)
    # maps to users table id column
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # relationship is a python shortcut
    owner: Mapped["User"] = relationship(back_populates="applications")
    events: Mapped[list["StatusEvent"]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        # Oldest first; id breaks ties between events saved in the same instant.
        order_by=lambda: (StatusEvent.changed_at, StatusEvent.id),
    )

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # When the password was last changed (UTC, whole seconds). Tokens issued
    # before this are rejected, so a reset logs out every other session.
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime)
    # Deleting a user deletes their applications (and, through those, their history).
    applications: Mapped[list["Application"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class StatusEvent(Base):
    __tablename__ = "status_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id"), index=True)
    from_status: Mapped[Status | None] = mapped_column(Enum(Status))
    to_status: Mapped[Status] = mapped_column(Enum(Status))
    changed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    application: Mapped["Application"] = relationship(back_populates="events")


class PasswordResetToken(Base):
    """A single-use password reset link. Only a hash of the token is stored."""

    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="reset_tokens")
