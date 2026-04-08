"""API tests for auth flow, protected endpoints, and rate limiting."""

from app.config import get_settings
from app.core.security import RateLimiter


settings = get_settings()


def test_protected_endpoint_requires_auth(unauth_client):
    resp = unauth_client.get("/api/packages/list")
    assert resp.status_code == 401


def test_protected_endpoint_rejects_invalid_token(unauth_client):
    resp = unauth_client.get(
        "/api/packages/list",
        headers={"Authorization": "Bearer invalid.token.value"},
    )
    assert resp.status_code == 401


def test_login_invalid_credentials_returns_401(unauth_client):
    resp = unauth_client.post(
        "/api/auth/login",
        json={"username": "wrong", "password": "wrong"},
    )
    assert resp.status_code == 401


def test_login_success_and_me_endpoint(unauth_client):
    login_resp = unauth_client.post(
        "/api/auth/login",
        json={"username": settings.auth_username, "password": settings.auth_password},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    me_resp = unauth_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["user"]["username"] == settings.auth_username


def test_login_rate_limited_after_threshold(unauth_client, monkeypatch):
    import app.api.dependencies as deps

    original_limiter = deps.rate_limiter
    monkeypatch.setattr(deps, "rate_limiter", RateLimiter(max_requests=2, window_seconds=60))

    try:
        r1 = unauth_client.post("/api/auth/login", json={"username": "x", "password": "x"})
        r2 = unauth_client.post("/api/auth/login", json={"username": "x", "password": "x"})
        r3 = unauth_client.post("/api/auth/login", json={"username": "x", "password": "x"})

        assert r1.status_code == 401
        assert r2.status_code == 401
        assert r3.status_code == 429
    finally:
        monkeypatch.setattr(deps, "rate_limiter", original_limiter)
