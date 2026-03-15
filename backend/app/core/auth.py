"""Authentication primitives for JWT-based API access."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt import InvalidTokenError

from app.config import get_settings

settings = get_settings()


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    """Create a short-lived JWT access token."""
    ttl_minutes = expires_minutes or settings.access_token_expire_minutes
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ttl_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Validate token signature and expiry."""
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def is_valid_credentials(username: str, password: str) -> bool:
    """Validate credentials from config/env for now (single admin identity)."""
    return username == settings.auth_username and password == settings.auth_password


def safe_decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return decode_access_token(token)
    except InvalidTokenError:
        return None
