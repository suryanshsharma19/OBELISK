"""Unit tests for API dependency helpers."""

import types

import pytest
from fastapi import HTTPException

import app.api.dependencies as deps
from app.core.auth import create_access_token


class DummyRequest:
    def __init__(self, token=None, cookie_token=None):
        self.client = types.SimpleNamespace(host="test-host")
        self.cookies = {}
        if cookie_token is not None:
            self.cookies["obelisk_access_token"] = cookie_token
        self._token = token


def test_get_current_user_from_bearer_credentials():
    token = create_access_token("tester")
    request = DummyRequest()
    creds = types.SimpleNamespace(scheme="Bearer", credentials=token)

    user = deps.get_current_user(request, creds)
    assert user["sub"] == "tester"


def test_get_current_user_missing_token_raises_401():
    with pytest.raises(HTTPException) as exc:
        deps.get_current_user(DummyRequest(), None)
    assert exc.value.status_code == 401


def test_get_current_user_invalid_token_raises_401():
    request = DummyRequest()
    creds = types.SimpleNamespace(scheme="Bearer", credentials="bad.token")

    with pytest.raises(HTTPException) as exc:
        deps.get_current_user(request, creds)
    assert exc.value.status_code == 401


def test_enforce_rate_limit_raises_429_when_blocked(monkeypatch):
    class FakeLimiter:
        def is_allowed(self, client_id):
            return False

    monkeypatch.setattr(deps, "rate_limiter", FakeLimiter())

    with pytest.raises(HTTPException) as exc:
        deps.enforce_rate_limit(DummyRequest())
    assert exc.value.status_code == 429
