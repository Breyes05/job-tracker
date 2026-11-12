"""Register, log in, and get the current user routes."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserRead, Token
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.rate_limit import failed_logins_by_email, login_attempts_by_ip

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def client_ip(request: Request) -> str:
    """The caller's IP address.

    In production, requests reach the app through Render's proxy, so the
    connection comes from the proxy. The proxy puts the original client's
    address first in X-Forwarded-For. A client can add its own entries to that
    header, so this is good enough for slowing down attackers but shouldn't be
    trusted for anything stronger; the per-email limit doesn't depend on it.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def too_many_attempts(retry_after: int) -> HTTPException:
    minutes = max(1, round(retry_after / 60))
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"Too many login attempts. Try again in {minutes} minute{'s' if minutes != 1 else ''}.",
        headers={"Retry-After": str(retry_after)},
    )


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Checks login information for existing user and password hash, returns new token."""
    email = form_data.username.strip().lower()
    ip = client_ip(request)

    # Refuse before checking the password, so a blocked attacker learns nothing.
    for limiter, key in ((login_attempts_by_ip, ip), (failed_logins_by_email, email)):
        wait = limiter.retry_after(key)
        if wait:
            raise too_many_attempts(wait)
    login_attempts_by_ip.hit(ip)

    user = db.scalar(select(User).where(User.email == form_data.username))

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if user is None or not verify_password(form_data.password, user.hashed_password):
        failed_logins_by_email.hit(email)
        raise credentials_error

    # A real user who mistyped a few times shouldn't stay penalized.
    failed_logins_by_email.reset(email)
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    """Return currently logged-in user."""
    return current_user