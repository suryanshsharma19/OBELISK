"""Integration tests — end-to-end flow through the API.

These tests verify the full request lifecycle from the HTTP layer
through the database, covering the most critical user paths.
"""

import pytest
from datetime import datetime, timezone

from app.db.models import Package, Alert, RegistryType, ThreatLevel


def test_health_check(client):
    """The /health endpoint should always be reachable."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


def test_full_package_lifecycle(client, db_session):
    """
    Seed a package → list → get detail → verify stats update.
    This mimics the core read path of the application.
    """
    # 1. Seed a package directly
    pkg = Package(
        name="lifecycle-pkg", version="1.0.0",
        registry=RegistryType.NPM,
        risk_score=42.0,
        threat_level=ThreatLevel.MEDIUM,
        is_malicious=False,
        analyzed_at=datetime.now(timezone.utc),
    )
    db_session.add(pkg)
    db_session.commit()

    # 2. List packages
    resp = client.get("/api/packages/list")
    data = resp.json()
    assert data["total"] == 1
    assert data["packages"][0]["name"] == "lifecycle-pkg"

    # 3. Stats should reflect the package
    resp = client.get("/api/stats/overview")
    stats = resp.json()
    assert stats["total_packages"] == 1
    assert stats["threat_distribution"]["medium"] == 1


def test_alert_lifecycle(client, db_session):
    """Create alert → list → read → resolve."""
    pkg = Package(
        name="alert-pkg", version="1.0.0",
        registry=RegistryType.NPM,
        risk_score=85.0,
        threat_level=ThreatLevel.CRITICAL,
        is_malicious=True,
        analyzed_at=datetime.now(timezone.utc),
    )
    db_session.add(pkg)
    db_session.flush()

    alert = Alert(
        package_id=pkg.id,
        title="Malicious package detected",
        description="High risk score",
        threat_level=ThreatLevel.CRITICAL,
    )
    db_session.add(alert)
    db_session.commit()

    # List
    resp = client.get("/api/alerts/")
    data = resp.json()
    assert data["total"] == 1

    # Update
    alert_id = data["alerts"][0]["id"]
    resp = client.put(f"/api/alerts/{alert_id}?is_resolved=true")
    assert resp.status_code == 200


def test_stats_trend_returns_data(client):
    """Trend endpoint should return data structure even with no packages."""
    resp = client.get("/api/stats/trend?days=3")
    assert resp.status_code == 200
    trend = resp.json()["trend"]
    assert len(trend) == 3
    assert all("date" in day for day in trend)


def test_crawler_status(client):
    """Crawler status should be accessible."""
    resp = client.get("/api/crawler/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "running" in data
