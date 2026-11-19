"""Request/response shapes (Pydantic).

These are separate from the database models on purpose: they control what
clients are allowed to send and what they get back, and Pydantic rejects
bad input (missing fields, wrong types) with a clear 422 error automatically.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, EmailStr

from app.models import Status


class ApplicationBase(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    role: str = Field(min_length=1, max_length=200)
    status: Status = Status.APPLIED
    date_applied: date = Field(default_factory=date.today)
    job_url: HttpUrl | None = None
    notes: str | None = None


class ApplicationCreate(ApplicationBase):
    """What a client sends to create an application."""


class ApplicationUpdate(BaseModel):
    """What a client sends to update one. Every field is optional so you can
    change just the status without resending everything."""

    company: str | None = Field(default=None, min_length=1, max_length=200)
    role: str | None = Field(default=None, min_length=1, max_length=200)
    status: Status | None = None
    date_applied: date | None = None
    job_url: HttpUrl | None = None
    notes: str | None = None


class ApplicationRead(ApplicationBase):
    """What the API sends back."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    job_url: str | None = None
    created_at: datetime
    updated_at: datetime
    followed_up_at: datetime | None = None


class StatusEventRead(BaseModel):
    """One entry in an application's status history."""

    model_config = ConfigDict(from_attributes=True)

    from_status: Status | None
    to_status: Status
    changed_at: datetime


class ImportRowProblem(BaseModel):
    row: int
    message: str


class ImportResult(BaseModel):
    """What happened when a CSV was imported."""

    imported: int
    skipped: list[ImportRowProblem]
    warnings: list[ImportRowProblem]


class WeekCount(BaseModel):
    week_start: date
    count: int


class StatsRead(BaseModel):
    """Summary of the current user's job search."""

    total: int
    responded: int
    interviewed: int
    offers: int
    rejected: int
    # Shares of `total` from 0 to 1, or null when there are no applications yet.
    response_rate: float | None
    interview_rate: float | None
    offer_rate: float | None
    median_days_to_response: float | None
    weekly: list[WeekCount]


class UserBase(BaseModel):
    email: EmailStr


class PasswordConfirm(BaseModel):
    """The current password, required before destructive account actions."""

    password: str = Field(min_length=1, max_length=72)


class UserCreate(UserBase):
    """What a client sends to create a user."""
    password: str = Field(min_length=8, max_length=72)


class UserRead(UserBase):
    """What API sends back."""

    # For pydantic behavior on SQLAlchemy Object
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"