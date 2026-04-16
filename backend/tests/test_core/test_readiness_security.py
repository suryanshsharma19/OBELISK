"""Tests for non-local security baseline readiness checks."""

from app.config import Settings
from app.core.readiness import check_security_baseline


def test_security_baseline_skipped_for_local_environment():
    report = check_security_baseline(Settings(environment="local"))

    assert report["ok"] is True
    assert report["status"] == "skipped"
    assert report["failures"] == []


def test_security_baseline_detects_weak_non_local_config():
    report = check_security_baseline(
        Settings(
            environment="production",
            secret_key="weak",
            auth_password="weak",
            secure_cookies=False,
            cors_origins="http://localhost:3000",
            allow_localhost_cors_in_non_local=False,
            enforce_strong_secrets=True,
        ),
    )

    assert report["ok"] is False
    assert report["status"] == "degraded"
    assert any("secret_key" in item for item in report["failures"])
    assert any("auth_password" in item for item in report["failures"])
    assert any("secure_cookies" in item for item in report["failures"])
    assert any("cors_origins" in item for item in report["failures"])


def test_security_baseline_passes_for_strong_non_local_config():
    report = check_security_baseline(
        Settings(
            environment="production",
            secret_key="ci_super_long_secret_key_value_1234567890",
            auth_password="CI-Strong-Pass-123!",
            secure_cookies=True,
            cors_origins="https://obelisk.example.com",
            allow_localhost_cors_in_non_local=False,
            enforce_strong_secrets=True,
        ),
    )

    assert report["ok"] is True
    assert report["status"] == "ready"
    assert report["failures"] == []
