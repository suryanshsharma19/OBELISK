"""Deterministic runtime-readiness unit tests for CI coverage stability."""

import pytest

from app.config import Settings
from app.core import readiness


def test_resolve_model_path_keeps_absolute_path():
    absolute_path = "/tmp/obelisk-model"

    resolved = readiness._resolve_model_path(absolute_path)

    assert str(resolved) == absolute_path


def test_run_named_check_reports_success_and_failure():
    success = readiness._run_named_check("sample", lambda: None)

    assert success["ok"] is True
    assert success["status"] == "ready"
    assert "reachable" in success["detail"]

    def _boom():
        raise RuntimeError("check failed")

    failure = readiness._run_named_check("sample", _boom)

    assert failure["ok"] is False
    assert failure["status"] == "degraded"
    assert failure["detail"] == "check failed"


def test_check_dependency_readiness_aggregates_failures(monkeypatch):
    def _fake_run_named_check(name, _func):
        if name == "Redis":
            return {"ok": False, "status": "degraded", "detail": "connection refused"}
        return {"ok": True, "status": "ready", "detail": f"{name} reachable"}

    monkeypatch.setattr(readiness, "_run_named_check", _fake_run_named_check)

    report = readiness.check_dependency_readiness()

    assert report["ok"] is False
    assert report["status"] == "degraded"
    assert report["checks"]["postgres"]["ok"] is True
    assert report["checks"]["redis"]["ok"] is False
    assert report["checks"]["neo4j"]["ok"] is True
    assert report["failures"] == ["redis: connection refused"]


def test_collect_runtime_readiness_calls_dependency_checks(monkeypatch):
    monkeypatch.setattr(readiness, "get_settings", lambda: Settings(environment="production"))
    monkeypatch.setattr(
        readiness,
        "check_model_artifacts",
        lambda _settings: {
            "ok": True,
            "status": "ready",
            "checked_at": "2026-01-01T00:00:00+00:00",
            "checks": {},
            "failures": [],
        },
    )
    monkeypatch.setattr(
        readiness,
        "check_security_baseline",
        lambda _settings: {
            "ok": True,
            "status": "ready",
            "checked_at": "2026-01-01T00:00:00+00:00",
            "checks": {},
            "failures": [],
        },
    )

    called = {"dependency": False}

    def _fake_dependency_report():
        called["dependency"] = True
        return {
            "ok": True,
            "status": "ready",
            "checked_at": "2026-01-01T00:00:00+00:00",
            "checks": {},
            "failures": [],
        }

    monkeypatch.setattr(readiness, "check_dependency_readiness", _fake_dependency_report)

    report = readiness.collect_runtime_readiness(include_dependencies=True)

    assert called["dependency"] is True
    assert report["ready"] is True
    assert report["status"] == "ready"


def test_run_startup_readiness_or_raise_ready_and_strict_failure(monkeypatch):
    monkeypatch.setattr(
        readiness,
        "collect_runtime_readiness",
        lambda include_dependencies: {
            "ready": True,
            "status": "ready",
            "checked_at": "2026-01-01T00:00:00+00:00",
            "checks": {},
            "failures": [],
        },
    )

    report = readiness.run_startup_readiness_or_raise(strict=False, include_dependencies=False)

    assert report["ready"] is True

    monkeypatch.setattr(
        readiness,
        "collect_runtime_readiness",
        lambda include_dependencies: {
            "ready": False,
            "status": "degraded",
            "checked_at": "2026-01-01T00:00:00+00:00",
            "checks": {},
            "failures": ["dependency::redis: connection refused"],
        },
    )

    with pytest.raises(RuntimeError, match="dependency::redis"):
        readiness.run_startup_readiness_or_raise(strict=True, include_dependencies=False)
