"""Register, log in, reset a password, and manage the current user."""

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.email import send_email
from app.models import PasswordResetToken, User
from app.schemas import (
    ForgotPasswordRequest,
    Message,
    PasswordConfirm,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserRead,
)
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.rate_limit import (
    failed_logins_by_email,
    login_attempts_by_ip,
    reset_requests_by_email,
    reset_requests_by_ip,
)

router = APIRouter(prefix="/auth", tags=["auth"])

RESET_TOKEN_LIFETIME = timedelta(hours=1)
# Where reset links point. Production sets this to the deployed frontend.
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
RESET_REQUESTED = "If an account exists for that email, we've sent a link to reset the password."


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def hash_token(token: str) -> str:
    """Reset tokens are stored hashed, so a database leak can't be used to reset passwords."""
    return hashlib.sha256(token.encode()).hexdigest()


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


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    payload: PasswordConfirm,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Permanently delete the logged-in user and all of their applications.

    Requires the current password, so a stolen token alone can't wipe an account.
    """
    if not verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Incorrect password")
    db.delete(current_user)
    db.commit()


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED, response_model=Message)
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Email a single-use reset link that expires in an hour.

    Responds the same way whether or not the account exists, so this can't be
    used to find out who has an account. The email is sent after the response,
    so response times don't give it away either.
    """
    email = payload.email.strip().lower()
    ip = client_ip(request)
    for limiter, key in ((reset_requests_by_ip, ip), (reset_requests_by_email, email)):
        wait = limiter.retry_after(key)
        if wait:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many reset requests. Try again later.",
                headers={"Retry-After": str(wait)},
            )
        limiter.hit(key)

    user = db.scalar(select(User).where(User.email == payload.email))
    if user is not None:
        # Only the newest link works.
        for old in user.reset_tokens:
            if old.used_at is None:
                old.used_at = utcnow()
        token = secrets.token_urlsafe(32)
        user.reset_tokens.append(
            PasswordResetToken(token_hash=hash_token(token), expires_at=utcnow() + RESET_TOKEN_LIFETIME)
        )
        db.commit()

        link = f"{FRONTEND_URL}/reset-password?token={token}"
        background_tasks.add_task(
            send_email,
            user.email,
            "Reset your Job Tracker password",
            f"Someone asked to reset the password for your Job Tracker account.\n\n"
            f"To choose a new password, open this link within the next hour:\n{link}\n\n"
            f"If you didn't ask for this, you can ignore this email; your password won't change.",
        )

    return Message(detail=RESET_REQUESTED)


@router.post("/reset-password", response_model=Message)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Set a new password using a reset link's token, and log out every other session."""
    reset = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_token(payload.token)))
    now = utcnow()
    if reset is None or reset.used_at is not None or reset.expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link is invalid or has expired. Request a new one.",
        )

    user = reset.user
    user.hashed_password = hash_password(payload.password)
    # Whole seconds, to match the "issued at" time in tokens.
    user.password_changed_at = now.replace(microsecond=0)
    for token in user.reset_tokens:
        if token.used_at is None:
            token.used_at = now
    db.commit()

    failed_logins_by_email.reset(user.email.lower())
    return Message(detail="Your password has been reset. You can log in now.")
