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


def test_startup_fails_when_db_bootstrap_fails(monkeypatch):
    from app.db.base import Base

    def _boom(*args, **kwargs):
        raise RuntimeError("db bootstrap failed")

    monkeypatch.setattr(Base.metadata, "create_all", _boom)

    with pytest.raises(RuntimeError, match="db bootstrap failed"):
        with TestClient(app):
            pass
