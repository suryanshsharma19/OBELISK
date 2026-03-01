"""Security utilities - API key validation, rate limiting."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.config import get_settings
from app.core.logging import setup_logger

logger = setup_logger(__name__)
settings = get_settings()

API_KEY_LENGTH = 64


def generate_api_key() -> str:
    return secrets.token_hex(API_KEY_LENGTH // 2)


def hash_api_key(api_key: str) -> str:
    """SHA-256 hash of an API key. We only store hashes."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def verify_api_key(provided_key: str, stored_hash: str) -> bool:
    provided_hash = hash_api_key(provided_key)
    return hmac.compare_digest(provided_hash, stored_hash)


def generate_secret_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def is_safe_redirect_url(url: str) -> bool:
    """Check that a redirect URL isn't an open-redirect."""
    if not url:
        return False
    if url.startswith("/") and not url.startswith("//"):
        return True
    # Allow our own frontend
    trusted_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    return any(url.startswith(origin) for origin in trusted_origins)


class RateLimiter:
    """Simple in-memory sliding-window rate limiter."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        # client_id -> [timestamps]
        self._store: dict[str, list[datetime]] = {}

    def is_allowed(self, client_id: str) -> bool:
        now = datetime.now(timezone.utc)
        cutoff = now - self.window

        # Purge stale entries
        timestamps = self._store.get(client_id, [])
        timestamps = [ts for ts in timestamps if ts > cutoff]

        if len(timestamps) >= self.max_requests:
            logger.warning("Rate limit exceeded for client %s", client_id)
            return False

        timestamps.append(now)
        self._store[client_id] = timestamps
        return True

    def reset(self, client_id: Optional[str] = None) -> None:
        if client_id:
            self._store.pop(client_id, None)
        else:
            self._store.clear()


rate_limiter = RateLimiter()
