#!/usr/bin/env python3
"""Critical API smoke checks for CI quality gates."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import get_settings
from app.main import app
from app.services import analysis_service


def _fail(message: str) -> int:
    print(f"FAIL: {message}")
    return 2


def main() -> int:
    settings = get_settings()

    async def _fake_fetch_metadata(name: str, version: str, registry: str):
        return {
            "name": name,
            "version": version,
            "registry": registry,
            "author": {
                "email": "smoke@example.com",
                "account_age_days": 365,
                "total_packages": 4,
                "has_verified_email": True,
                "github_repos": 2,
                "previous_downloads": 100,
            },
            "dependencies": {"dep-one": "1.0.0"},
            "scripts": {"postinstall": "echo smoke"},
        }

    original_fetch = analysis_service._fetch_metadata
    analysis_service._fetch_metadata = _fake_fetch_metadata

    try:
        with TestClient(app) as client:
            health = client.get("/health")
            if health.status_code != 200:
                return _fail(f"/health returned {health.status_code}")

            ready = client.get("/health/ready")
            if ready.status_code != 200:
                return _fail(f"/health/ready returned {ready.status_code}: {ready.text}")

            login = client.post(
                "/api/auth/login",
                json={
                    "username": settings.auth_username,
                    "password": settings.auth_password,
                },
            )
            if login.status_code != 200:
                return _fail(f"/api/auth/login returned {login.status_code}")

            token = login.json().get("access_token")
            if not token:
                return _fail("Login response did not include access_token")

            headers = {"Authorization": f"Bearer {token}"}

            package_list = client.get("/api/packages/list", headers=headers)
            if package_list.status_code != 200:
                return _fail(f"/api/packages/list returned {package_list.status_code}")

            analyze_payload = {
                "name": "smoke-analyze-pkg",
                "version": "1.0.0",
                "registry": "npm",
                "code": "const cp = require('child_process'); cp.exec('echo smoke');",
            }
            analyze = client.post("/api/packages/analyze", json=analyze_payload, headers=headers)
            if analyze.status_code != 200:
                return _fail(f"/api/packages/analyze returned {analyze.status_code}")

            body = analyze.json()
            if "package" not in body or "analysis" not in body:
                return _fail("Analyze response missing package/analysis sections")

            print(json.dumps({
                "health": health.json(),
                "ready": ready.json().get("status"),
                "analyze_threat_level": body["analysis"].get("threat_level"),
            }, indent=2))
    finally:
        analysis_service._fetch_metadata = original_fetch

    print("PASS: critical endpoint smoke checks succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
