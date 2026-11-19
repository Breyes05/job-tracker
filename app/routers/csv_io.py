"""Export applications to CSV, and import them from a spreadsheet."""

import csv
import io
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Application, Status, User
from app.routers.applications import record_status_change, to_db_values
from app.schemas import ApplicationCreate, ImportResult, ImportRowProblem

router = APIRouter(prefix="/applications", tags=["import and export"])

EXPORT_COLUMNS = ["company", "role", "status", "date_applied", "job_url", "notes", "created_at"]
MAX_IMPORT_BYTES = 1_000_000
MAX_IMPORT_ROWS = 1000

# Spreadsheets name columns all sorts of ways; match the common ones.
HEADER_ALIASES = {
    "company": {"company", "company name", "employer", "organization"},
    "role": {"role", "position", "title", "job title", "job"},
    "status": {"status", "stage"},
    "date_applied": {"date applied", "date", "applied", "applied on", "application date"},
    "job_url": {"job url", "url", "link", "job link", "posting", "job posting"},
    "notes": {"notes", "note", "comments"},
}

STATUS_ALIASES = {
    Status.APPLIED: {"applied", "submitted", "sent", "pending", "waiting"},
    Status.INTERVIEWING: {
        "interviewing", "interview", "interviews", "oa", "online assessment",
        "phone screen", "screening", "final round", "onsite",
    },
    Status.OFFER: {"offer", "offered", "accepted"},
    Status.REJECTED: {"rejected", "rejection", "declined", "no"},
}

DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%b %d %Y", "%B %d %Y", "%b %d, %Y", "%B %d, %Y"]


def normalize(text: str) -> str:
    return " ".join(text.replace("_", " ").strip().lower().split())


def map_headers(fieldnames: list[str]) -> dict[str, str]:
    """Map our field names to the CSV's own column names."""
    mapping = {}
    for column in fieldnames:
        for field, aliases in HEADER_ALIASES.items():
            if normalize(column) in aliases and field not in mapping:
                mapping[field] = column
    return mapping


def parse_status(raw: str) -> Status | None:
    value = normalize(raw)
    if not value:
        return Status.APPLIED
    for status_value, aliases in STATUS_ALIASES.items():
        if value in aliases:
            return status_value
    return None


def parse_date(raw: str) -> date | None:
    value = " ".join(raw.strip().split())
    if not value:
        return date.today()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def first_error(error: ValidationError) -> str:
    problem = error.errors()[0]
    field = problem["loc"][-1] if problem["loc"] else "row"
    return f"{field}: {problem['msg']}"


@router.get("/export")
def export_applications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Download every application as a CSV file."""
    applications = db.scalars(
        select(Application)
        .where(Application.user_id == current_user.id)
        .order_by(Application.date_applied.desc(), Application.id.desc())
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(EXPORT_COLUMNS)
    for a in applications:
        writer.writerow([
            a.company, a.role, a.status.value, a.date_applied.isoformat(),
            a.job_url or "", a.notes or "", a.created_at.isoformat(timespec="seconds"),
        ])

    filename = f"job-applications-{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import", response_model=ImportResult)
async def import_applications(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create applications from a CSV with at least Company and Role columns.

    Valid rows are imported and invalid ones are reported back by row number,
    so one bad row doesn't block the rest. Everything valid is saved in one
    transaction.
    """
    content = await file.read(MAX_IMPORT_BYTES + 1)
    if len(content) > MAX_IMPORT_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="The file is larger than 1 MB.")
    try:
        text = content.decode("utf-8-sig")  # Excel adds a byte-order mark
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    headers = map_headers(reader.fieldnames or [])
    missing = [name for name in ("company", "role") if name not in headers]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Couldn't find a column for: {', '.join(missing)}. Add a header row with Company and Role columns.",
        )

    imported = 0
    skipped: list[ImportRowProblem] = []
    warnings: list[ImportRowProblem] = []

    rows_seen = 0
    for row in reader:
        # The spreadsheet's own line number (blank lines are skipped but still counted).
        row_number = reader.line_num
        rows_seen += 1
        if rows_seen > MAX_IMPORT_ROWS:
            skipped.append(ImportRowProblem(row=row_number, message=f"Only the first {MAX_IMPORT_ROWS} rows are imported."))
            break

        def cell(field: str) -> str:
            column = headers.get(field)
            return (row.get(column) or "").strip() if column else ""

        if not any((value or "").strip() for value in row.values() if isinstance(value, str)):
            continue  # blank line

        status_value = parse_status(cell("status"))
        if status_value is None:
            warnings.append(ImportRowProblem(row=row_number, message=f"Unknown status '{cell('status')}', imported as Applied."))
            status_value = Status.APPLIED

        applied_on = parse_date(cell("date_applied"))
        if applied_on is None:
            skipped.append(ImportRowProblem(row=row_number, message=f"Couldn't read the date '{cell('date_applied')}'. Use YYYY-MM-DD or MM/DD/YYYY."))
            continue

        try:
            payload = ApplicationCreate(
                company=cell("company"),
                role=cell("role"),
                status=status_value,
                date_applied=applied_on,
                job_url=cell("job_url") or None,
                notes=cell("notes") or None,
            )
        except ValidationError as error:
            skipped.append(ImportRowProblem(row=row_number, message=first_error(error)))
            continue

        application = Application(**to_db_values(payload.model_dump()), user_id=current_user.id)
        record_status_change(application, old_status=None)
        db.add(application)
        imported += 1

    db.commit()
    return ImportResult(imported=imported, skipped=skipped, warnings=warnings)
