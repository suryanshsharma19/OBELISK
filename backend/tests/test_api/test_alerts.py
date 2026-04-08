"""Tests for the /api/alerts routes."""

import pytest
from datetime import datetime, timezone

from app.db.models import Alert, Package, RegistryType, ThreatLevel


def _seed_alert(db, title="Test Alert", threat_level=ThreatLevel.HIGH):
    """Helper: insert a package + linked alert, return alert id."""
    pkg = Package(
        name="evil-pkg", version="0.0.1",
        registry=RegistryType.NPM,
        risk_score=80.0, threat_level=ThreatLevel.CRITICAL,
        is_malicious=True,
        analyzed_at=datetime.now(timezone.utc),
    )
    db.add(pkg)
    db.flush()

    alert = Alert(
        package_id=pkg.id,
        title=title,
        description="Suspicious package detected",
        threat_level=threat_level,
        is_read=False,
        is_resolved=False,
    )
    db.add(alert)
    db.commit()
    return alert.id


def test_list_alerts_empty(client):
    """Empty DB should return zero alerts."""
    resp = client.get("/api/alerts/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0


def test_list_alerts_with_data(client, db_session):
    """Seeded alerts should appear in the listing."""
    _seed_alert(db_session)
    resp = client.get("/api/alerts/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["unread_count"] >= 1


def test_get_alert_detail(client, db_session):
    """GET /api/alerts/{id} should return full alert data."""
    aid = _seed_alert(db_session, title="Detail test")
    resp = client.get(f"/api/alerts/{aid}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Detail test"
    assert body["is_resolved"] is False


def test_get_alert_not_found(client):
    resp = client.get("/api/alerts/9999")
    assert resp.status_code == 404


def test_update_alert_mark_read(client, db_session):
    """PUT should mark an alert as read."""
    aid = _seed_alert(db_session)
    resp = client.put(f"/api/alerts/{aid}?is_read=true")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Alert updated"


def test_update_alert_not_found(client):
    resp = client.put("/api/alerts/9999?is_read=true")
    assert resp.status_code == 404
