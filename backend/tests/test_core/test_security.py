"""Unit tests for security utilities and in-memory rate limiting."""

from app.core.security import (
    RateLimiter,
    generate_api_key,
    generate_secret_token,
    hash_api_key,
    is_safe_redirect_url,
    verify_api_key,
)
from app.config import get_settings


settings = get_settings()


def test_api_key_hash_and_verify_roundtrip():
    api_key = generate_api_key()
    hashed = hash_api_key(api_key)

    assert len(api_key) == 64
    assert verify_api_key(api_key, hashed) is True
    assert verify_api_key("wrong-key", hashed) is False


def test_generate_secret_token_has_entropy():
    token_a = generate_secret_token()
    token_b = generate_secret_token()
    assert token_a != token_b
    assert len(token_a) > 20


def test_safe_redirect_url_allows_local_paths_and_known_origin():
    assert is_safe_redirect_url("/dashboard") is True

    localhost_allowed = settings.environment == "local" or (
        "http://localhost:3000" in settings.cors_origins
    )
    assert is_safe_redirect_url("http://localhost:3000/alerts") is localhost_allowed

    assert is_safe_redirect_url("http://evil.example/steal") is False
    assert is_safe_redirect_url("//evil.example") is False


def test_rate_limiter_blocks_after_limit_and_resets():
    limiter = RateLimiter(max_requests=2, window_seconds=60)

    assert limiter.is_allowed("client-1") is True
    assert limiter.is_allowed("client-1") is True
    assert limiter.is_allowed("client-1") is False

    limiter.reset("client-1")
    assert limiter.is_allowed("client-1") is True
