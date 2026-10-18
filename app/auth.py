"""Password hashing + JWT creation."""

import os

from datetime import datetime, timedelta, timezone
import bcrypt
import jwt

# Dev-only fallback so local runs, testing, and CI work w/o setup.
# Prod must use a real SECRET_KEY as an env var.
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me-not-for-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def hash_password(password: str) -> str:
    # encoe password, hash with unique salt
    pass_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pass_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    # match password bytes to hash bytes
    pass_bytes = password.encode('utf-8')
    hash_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(pass_bytes, hash_bytes)

def create_access_token(user_id: int) -> str:
    # create signed jwt to identify users, 30 min expiration
    # why use jwt
    sub = str(user_id)
    exp = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": sub, "exp": exp}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)