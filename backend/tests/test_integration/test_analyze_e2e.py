"""End-to-end integration test for the analyze pipeline."""

from __future__ import annotations

from app.core.auth import create_access_token
from app.db.models import Analysis, Package
from app.models.analysis import DetectionResult
from app.services import analysis_service


def test_analyze_flow_e2e_with_cache_and_websocket(client, db_session, monkeypatch):
    """Analyze API should execute detectors, persist, cache, and emit websocket events."""

    async def _fake_fetch_metadata(name: str, version: str, registry: str):
        return {
            "name": name,
            "version": version,
            "registry": registry,
            "author": {
                "email": "maintainer@example.com",
                "account_age_days": 400,
                "total_packages": 8,
                "has_verified_email": True,
                "github_repos": 5,
                "previous_downloads": 1000,
            },
            "dependencies": {"dep-safe": "1.2.3", "dep-mid": "4.5.6"},
            "scripts": {"postinstall": "echo setup"},
        }

    detector_calls = {
        "typosquatting": 0,
        "code_analysis": 0,
        "behavior": 0,
        "maintainer": 0,
        "dependency": 0,
    }

    def _detector(name: str, score: float):
        async def _run(**kwargs):
            detector_calls[name] += 1
            return DetectionResult(
                score=score,
                confidence=0.9,
                evidence={"detector": name, "kwargs_seen": sorted(kwargs.keys())},
            )

        return _run

    cache_store: dict[str, dict] = {}

    def _get_cache(key: str):
        cached = cache_store.get(key)
        if cached is None:
            return None, "miss"
        return cached, "hit"

    def _set_cache(key: str, data: dict):
        cache_store[key] = data

    monkeypatch.setattr(analysis_service, "_fetch_metadata", _fake_fetch_metadata)
    monkeypatch.setattr(analysis_service._typosquat, "run", _detector("typosquatting", 10.0))
    monkeypatch.setattr(analysis_service._code_analyzer, "run", _detector("code_analysis", 35.0))
    monkeypatch.setattr(analysis_service._behavior, "run", _detector("behavior", 20.0))
    monkeypatch.setattr(analysis_service._anomaly, "run", _detector("maintainer", 5.0))
    monkeypatch.setattr(analysis_service._gnn, "run", _detector("dependency", 15.0))
    monkeypatch.setattr(analysis_service, "_persist_to_neo4j", lambda *args, **kwargs: None)
    monkeypatch.setattr(analysis_service, "_get_cached_result", _get_cache)
    monkeypatch.setattr(analysis_service, "_cache_result", _set_cache)

    payload = {
        "name": "e2e-analyze-pkg",
        "version": "1.2.3",
        "registry": "npm",
        "code": "const cp = require('child_process'); cp.exec('echo test');",
    }

    token = create_access_token("ws-e2e-user")

    with client.websocket_connect(f"/ws?token={token}") as websocket:
        first_resp = client.post("/api/packages/analyze", json=payload)
        assert first_resp.status_code == 200
        first_data = first_resp.json()

        first_event = websocket.receive_json()
        assert first_event["type"] == "analysis_complete"
        assert first_event["data"]["package"]["name"] == payload["name"]
        assert first_event["data"]["from_cache"] is False

        # Second request should hit cache and skip detector execution.
        second_resp = client.post("/api/packages/analyze", json=payload)
        assert second_resp.status_code == 200
        second_data = second_resp.json()

        second_event = websocket.receive_json()
        assert second_event["type"] == "analysis_complete"
        assert second_event["data"]["package"]["name"] == payload["name"]
        assert second_event["data"]["from_cache"] is True

    assert first_data == second_data

    # All critical detectors ran on first analysis.
    assert detector_calls == {
        "typosquatting": 1,
        "code_analysis": 1,
        "behavior": 1,
        "maintainer": 1,
        "dependency": 1,
    }

    package_row = (
        db_session.query(Package)
        .filter(Package.name == payload["name"], Package.version == payload["version"])
        .first()
    )
    assert package_row is not None

    analysis_rows = db_session.query(Analysis).filter(Analysis.package_id == package_row.id).all()
    assert len(analysis_rows) == 1

    cache_key = f"analysis:{payload['registry']}:{payload['name']}:{payload['version']}"
    assert cache_key in cache_store
