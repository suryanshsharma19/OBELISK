"""Unit tests for JWT auth primitives."""

import pytest
from jwt import InvalidTokenError

from app.config import get_settings
from app.core.auth import (
    create_access_token,
    decode_access_token,
    is_valid_credentials,
    safe_decode_access_token,
)


settings = get_settings()


def test_create_and_decode_access_token_roundtrip():
    token = create_access_token("alice", expires_minutes=5)
    payload = decode_access_token(token)
    assert payload["sub"] == "alice"
    assert "exp" in payload


def test_decode_access_token_expired_raises():
    token = create_access_token("bob", expires_minutes=-1)
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_safe_decode_access_token_invalid_returns_none():
    assert safe_decode_access_token("not-a-valid-token") is None


def test_is_valid_credentials_matches_configured_admin():
    assert is_valid_credentials(settings.auth_username, settings.auth_password) is True
    assert is_valid_credentials("bad-user", "bad-password") is False
