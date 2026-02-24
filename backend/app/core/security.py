"""
Security utilities — API key validation, rate limiting helpers,
and basic token generation for the OBELISK API.

Nothing overly complex for now; we can bolt on OAuth2 / JWT later
if the project needs proper user auth.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.config import get_settings
from app.core.logging import setup_logger

logger = setup_logger(__name__)
settings = get_settings()

# Length of generated API keys (hex characters)
API_KEY_LENGTH = 64


def generate_api_key() -> str:
    """Create a cryptographically-random API key (hex string)."""
    return secrets.token_hex(API_KEY_LENGTH // 2)


def hash_api_key(api_key: str) -> str:
    """
    One‑way SHA‑256 hash of an API key.

    We never store raw keys in the database — only hashes.
    """
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def verify_api_key(provided_key: str, stored_hash: str) -> bool:
    """Constant-time comparison to prevent timing attacks."""
    provided_hash = hash_api_key(provided_key)
    return hmac.compare_digest(provided_hash, stored_hash)


def generate_secret_token(nbytes: int = 32) -> str:
    """Return a URL-safe random token (e.g. for CSRF, webhooks)."""
    return secrets.token_urlsafe(nbytes)


def is_safe_redirect_url(url: str) -> bool:
    """
    Basic check that a redirect URL is relative or points to a
    trusted domain.  Prevents open-redirect vulnerabilities.
    """
    if not url:
        return False
    # Allow relative paths
    if url.startswith("/") and not url.startswith("//"):
        return True
    # Allow our own frontend
    trusted_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    return any(url.startswith(origin) for origin in trusted_origins)


class RateLimiter:
    """
    Simple in-memory sliding-window rate limiter.

    For production you'd swap this out for a Redis-backed limiter,
    but this keeps the local-dev experience dependency-free.
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        # key → list[datetime]  (request timestamps)
        self._store: dict[str, list[datetime]] = {}

    def is_allowed(self, client_id: str) -> bool:
        """Return True if the client hasn't exceeded the rate limit."""
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
        """Clear rate-limit counters (useful in tests)."""
        if client_id:
            self._store.pop(client_id, None)
        else:
            self._store.clear()


# Module-level singleton — import and use directly
rate_limiter = RateLimiter()
