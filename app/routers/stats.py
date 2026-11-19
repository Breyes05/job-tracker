"""Summary statistics for the current user's job search, computed from the status history."""

from datetime import date, timedelta
from statistics import median

from fastapi import APIRouter, Depends
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Application, Status, StatusEvent, User
from app.schemas import StatsRead, WeekCount

router = APIRouter(prefix="/stats", tags=["stats"])

WEEKS_SHOWN = 8

# A company "responded" once an application moves past Applied in any direction.
RESPONDED = (Status.INTERVIEWING, Status.OFFER, Status.REJECTED)
# Reaching Offer implies there was an interview, even if the card skipped the column.
INTERVIEWED = (Status.INTERVIEWING, Status.OFFER)


def ever_reached(db: Session, user_id: int, statuses: tuple[Status, ...]) -> int:
    """How many of this user's applications have ever had one of these statuses.

    Uses the history, not the current status, so moving a card back doesn't
    erase progress that really happened.
    """
    query = (
        select(func.count(distinct(StatusEvent.application_id)))
        .join(Application, StatusEvent.application_id == Application.id)
        .where(Application.user_id == user_id, StatusEvent.to_status.in_(statuses))
    )
    return db.scalar(query)


def days_to_first_response(db: Session, user_id: int) -> list[int]:
    """For each application that moved out of Applied, days from applying to that first move.

    Only counts moves recorded *from* Applied, so applications added after the
    company had already replied (or backfilled before history existed) don't
    produce made-up response times.

    `changed_at` is stored in UTC while `date_applied` is the user's own calendar
    date, so a result can be off by a day near midnight. Close enough for a median.
    """
    query = (
        select(Application.date_applied, func.min(StatusEvent.changed_at))
        .join(StatusEvent, StatusEvent.application_id == Application.id)
        .where(
            Application.user_id == user_id,
            StatusEvent.from_status == Status.APPLIED,
            StatusEvent.to_status.in_(RESPONDED),
        )
        .group_by(Application.id, Application.date_applied)
    )
    return [max(0, (first_response.date() - applied).days) for applied, first_response in db.execute(query)]


def applications_per_week(db: Session, user_id: int, today: date) -> list[WeekCount]:
    """Applications by the week they were applied to, for the last WEEKS_SHOWN weeks (Monday start)."""
    this_week = today - timedelta(days=today.weekday())
    first_week = this_week - timedelta(weeks=WEEKS_SHOWN - 1)

    counts = {first_week + timedelta(weeks=i): 0 for i in range(WEEKS_SHOWN)}
    dates = db.scalars(
        select(Application.date_applied).where(
            Application.user_id == user_id, Application.date_applied >= first_week
        )
    )
    for applied in dates:
        week = applied - timedelta(days=applied.weekday())
        if week in counts:  # skips dates in the future
            counts[week] += 1
    return [WeekCount(week_start=week, count=count) for week, count in counts.items()]


def rate(part: int, total: int) -> float | None:
    return round(part / total, 4) if total else None


@router.get("", response_model=StatsRead)
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Response rate, interview rate, offers, time to first response, and weekly activity."""
    total = db.scalar(select(func.count()).select_from(Application).where(Application.user_id == current_user.id))
    responded = ever_reached(db, current_user.id, RESPONDED)
    interviewed = ever_reached(db, current_user.id, INTERVIEWED)
    offers = ever_reached(db, current_user.id, (Status.OFFER,))
    rejected = ever_reached(db, current_user.id, (Status.REJECTED,))
    response_days = days_to_first_response(db, current_user.id)

    return StatsRead(
        total=total,
        responded=responded,
        interviewed=interviewed,
        offers=offers,
        rejected=rejected,
        response_rate=rate(responded, total),
        interview_rate=rate(interviewed, total),
        offer_rate=rate(offers, total),
        median_days_to_response=median(response_days) if response_days else None,
        weekly=applications_per_week(db, current_user.id, date.today()),
    )
