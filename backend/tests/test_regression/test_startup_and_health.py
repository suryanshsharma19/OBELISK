"""Regression tests for startup behavior and health contract."""

import pytest
from fastapi.testclient import TestClient


from app.main import app


def test_app_root_contract(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "OBELISK"
    assert body["status"] == "operational"


def test_health_endpoint_contract(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "obelisk-backend"
    assert "startup_readiness" in data


def test_readiness_endpoint_contract_ready(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.health.collect_runtime_readiness",
        lambda include_dependencies=True: {
            "status": "ready",
            "ready": True,
            "checked_at": "2026-01-01T00:00:00+00:00",
            "checks": {},
            "failures": [],
        },
    )

    resp = client.get("/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["runtime"]["ready"] is True


def test_readiness_endpoint_contract_degraded(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.health.collect_runtime_readiness",
        lambda include_dependencies=True: {
            "status": "degraded",
            "ready": False,
            "checked_at": "2026-01-01T00:00:00+00:00",
            "checks": {},
            "failures": ["dependency::redis: connection refused"],
        },
    )

    resp = client.get("/health/ready")
    assert resp.status_code == 503
    data = resp.json()
    assert data["status"] == "degraded"
    assert data["runtime"]["ready"] is False
    assert data["runtime"]["failures"]


def test_worker_health_endpoint_contract(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.health.collect_worker_observability",
        lambda: {
            "worker": {"healthy": True, "workers": ["celery@w1"]},
            "queue": {"name": "celery", "depth": 3},
        },
    )

    resp = client.get("/health/worker")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["worker"]["healthy"] is True
    assert data["queue"]["depth"] == 3


def test_worker_health_endpoint_degraded(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.health.collect_worker_observability",
        lambda: {
            "worker": {"healthy": False, "workers": [], "error": "timeout"},
            "queue": {"name": "celery", "depth": 0},
        },
    )

    resp = client.get("/health/worker")
    assert resp.status_code == 503
    data = resp.json()
    assert data["status"] == "degraded"
    assert data["worker"]["healthy"] is False


def test_metrics_endpoint_contract(client, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.health.render_metrics",
        lambda: (b"test_metric 1\n", "text/plain; version=0.0.4"),
    )

    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "test_metric 1" in resp.text
    assert "text/plain" in resp.headers.get("content-type", "")


def test_startup_fails_when_db_bootstrap_fails(monkeypatch):
    from app.db.base import Base

    def _boom(*args, **kwargs):
        raise RuntimeError("db bootstrap failed")

    monkeypatch.setattr(Base.metadata, "create_all", _boom)

    with pytest.raises(RuntimeError, match="db bootstrap failed"):
        with TestClient(app):
            pass
