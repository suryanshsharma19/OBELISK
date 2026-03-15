"""Shared FastAPI dependencies."""

from collections.abc import Generator

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.auth import safe_decode_access_token
from app.core.security import rate_limiter
from app.db.session import SessionLocal

security = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    token = None

    if credentials and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
    elif request.cookies.get("obelisk_access_token"):
        token = request.cookies.get("obelisk_access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    payload = safe_decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload


def enforce_rate_limit(request: Request) -> None:
    client_id = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
