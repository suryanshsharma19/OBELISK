"""Tests for the /api/packages routes."""

import pytest
from datetime import datetime, timezone

from app.db.models import Package, RegistryType, ThreatLevel


def test_list_packages_empty(client):
    """Listing packages on a fresh DB should return an empty list."""
    resp = client.get("/api/packages/list")
    assert resp.status_code == 200
    data = resp.json()
    assert data["packages"] == []
    assert data["total"] == 0


def test_list_packages_returns_seeded(client, db_session):
    """Packages inserted via the DB should appear in the listing."""
    pkg = Package(
        name="express",
        version="4.18.0",
        registry=RegistryType.npm,
        risk_score=12.5,
        threat_level=ThreatLevel.low,
        is_malicious=False,
        analyzed_at=datetime.now(timezone.utc),
    )
    db_session.add(pkg)
    db_session.commit()

    resp = client.get("/api/packages/list")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["packages"][0]["name"] == "express"


def test_list_packages_filter_threat_level(client, db_session):
    """Filter by threat_level should only return matching packages."""
    for name, level in [("safe-pkg", ThreatLevel.safe), ("bad-pkg", ThreatLevel.high)]:
        db_session.add(
            Package(
                name=name, version="1.0.0",
                registry=RegistryType.npm,
                risk_score=50 if level == ThreatLevel.high else 5,
                threat_level=level,
                analyzed_at=datetime.now(timezone.utc),
            )
        )
    db_session.commit()

    resp = client.get("/api/packages/list?threat_level=high")
    data = resp.json()
    assert data["total"] == 1
    assert data["packages"][0]["name"] == "bad-pkg"


def test_list_packages_pagination(client, db_session):
    """Skip / limit parameters should control the returned window."""
    for i in range(5):
        db_session.add(
            Package(
                name=f"pkg-{i}", version="1.0.0",
                registry=RegistryType.npm,
                risk_score=0, threat_level=ThreatLevel.safe,
                analyzed_at=datetime.now(timezone.utc),
            )
        )
    db_session.commit()

    resp = client.get("/api/packages/list?skip=2&limit=2")
    data = resp.json()
    assert len(data["packages"]) == 2
    assert data["total"] == 5


def test_get_package_not_found(client):
    """Requesting a non-existent package should 404."""
    resp = client.get("/api/packages/9999")
    assert resp.status_code == 404
