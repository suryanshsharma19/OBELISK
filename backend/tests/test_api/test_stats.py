"""Tests for the /api/stats routes."""

import pytest
from datetime import datetime, timezone

from app.db.models import Package, RegistryType, ThreatLevel


def test_overview_empty(client):
    """Empty DB should return all zeroes."""
    resp = client.get("/api/stats/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_packages"] == 0
    assert data["malicious_packages"] == 0
    assert data["detection_rate"] == 0.0


def test_overview_with_packages(client, db_session):
    """Stats should reflect inserted packages."""
    for name, mal in [("safe", False), ("evil", True)]:
        db_session.add(
            Package(
                name=name, version="1.0.0",
                registry=RegistryType.npm,
                risk_score=90 if mal else 5,
                threat_level=ThreatLevel.critical if mal else ThreatLevel.safe,
                is_malicious=mal,
                analyzed_at=datetime.now(timezone.utc),
            )
        )
    db_session.commit()

    resp = client.get("/api/stats/overview")
    data = resp.json()
    assert data["total_packages"] == 2
    assert data["malicious_packages"] == 1
    assert data["detection_rate"] == 50.0


def test_overview_threat_distribution(client, db_session):
    """Distribution dict should map threat levels to counts."""
    db_session.add(
        Package(
            name="medium-pkg", version="1.0.0",
            registry=RegistryType.npm,
            risk_score=45, threat_level=ThreatLevel.medium,
            analyzed_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    data = client.get("/api/stats/overview").json()
    assert data["threat_distribution"]["medium"] == 1


def test_trend_default_days(client):
    """Trend endpoint should return 7 data points by default."""
    resp = client.get("/api/stats/trend")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["trend"]) == 7


def test_trend_custom_days(client):
    """Custom day count should be respected."""
    resp = client.get("/api/stats/trend?days=3")
    data = resp.json()
    assert len(data["trend"]) == 3
