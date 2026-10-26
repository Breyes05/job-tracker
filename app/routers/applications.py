"""CRUD endpoints for job applications."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Application, Status, User
from app.schemas import ApplicationCreate, ApplicationRead, ApplicationUpdate

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
    for field, value in updates.items():
        setattr(application, field, value)
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
