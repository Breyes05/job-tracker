"""CRUD endpoints for job applications."""

from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Application, Status, StatusEvent, User
from app.schemas import ApplicationCreate, ApplicationRead, ApplicationUpdate, StatusEventRead

router = APIRouter(prefix="/applications", tags=["applications"])

SORTABLE_FIELDS = {
    "date_applied": Application.date_applied,
    "company": Application.company,
    "created_at": Application.created_at,
}


def to_db_values(data: dict) -> dict:
    """Pydantic's HttpUrl is an object; the database column stores plain text."""
    if data.get("job_url") is not None:
        data["job_url"] = str(data["job_url"])
    return data


# A change that exactly undoes the previous one within this window is treated as
# a correction (a misclick or a drag into the wrong column), not as history.
CORRECTION_WINDOW = timedelta(minutes=5)


def utcnow() -> datetime:
    """Current UTC time as a naive datetime, matching how timestamps are stored.

    Kept as a function so tests can move the clock forward.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def record_status_change(application: Application, old_status: Status | None) -> None:
    """Add a status event for this change, or remove the last one if this undoes it.

    Called before commit, so the event is saved in the same transaction as the
    status itself: both are saved, or neither is.
    """
    new_status = application.status
    if new_status == old_status:
        return

    now = utcnow()
    last = application.events[-1] if application.events else None
    is_quick_undo = (
        last is not None
        and last.from_status is not None
        and last.from_status == new_status
        and last.to_status == old_status
        and now - last.changed_at < CORRECTION_WINDOW
    )
    if is_quick_undo:
        application.events.remove(last)  # delete-orphan deletes the row on commit
        return

    application.events.append(StatusEvent(from_status=old_status, to_status=new_status, changed_at=now))


def get_application_or_404(application_id: int, db: Session, user: User) -> Application:
    application = db.get(Application, application_id)
    if application is None or application.user_id != user.id:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    application = Application(**to_db_values(payload.model_dump()), user_id=current_user.id)
    record_status_change(application, old_status=None)
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get("", response_model=list[ApplicationRead])
def list_applications(
    status: Status | None = None,
    company: str | None = Query(default=None, description="Case-insensitive partial match"),
    sort_by: Literal["date_applied", "company", "created_at"] = "date_applied",
    order: Literal["asc", "desc"] = "desc",
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Application).where(Application.user_id == current_user.id)
    if status is not None:
        query = query.where(Application.status == status)
    if company:
        query = query.where(Application.company.ilike(f"%{company}%"))

    column = SORTABLE_FIELDS[sort_by]
    query = query.order_by(column.desc() if order == "desc" else column.asc())
    query = query.limit(limit).offset(offset)
    return db.scalars(query).all()


@router.get("/{application_id}", response_model=ApplicationRead)
def get_application(
    application_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    return get_application_or_404(application_id, db, current_user)


@router.get("/{application_id}/history", response_model=list[StatusEventRead])
def get_application_history(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Every status change for one application, oldest first."""
    application = get_application_or_404(application_id, db, current_user)
    return application.events


@router.patch("/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: int, 
    payload: ApplicationUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    application = get_application_or_404(application_id, db, current_user)
    # exclude_unset: only touch fields the client actually sent
    updates = to_db_values(payload.model_dump(exclude_unset=True))
    old_status = application.status
    for field, value in updates.items():
        setattr(application, field, value)
    record_status_change(application, old_status)
    db.commit()
    db.refresh(application)
    return application


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    application = get_application_or_404(application_id, db, current_user)
    db.delete(application)
    db.commit()
