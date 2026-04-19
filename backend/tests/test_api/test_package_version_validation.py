"""Validation tests for registry-specific package versions."""


def test_analyze_accepts_pypi_pep440_style_version(client, monkeypatch):
    async def _fake_analyze_package(**kwargs):
        return {
            "package": {
                "id": 1,
                "name": kwargs["name"],
                "version": kwargs["version"],
                "registry": kwargs["registry"],
                "risk_score": 0.0,
                "threat_level": "safe",
                "is_malicious": False,
            },
            "analysis": {
                "risk_score": 0.0,
                "threat_level": "safe",
                "is_malicious": False,
                "confidence": 1.0,
                "breakdown": {},
            },
            "detection_details": {},
        }

    monkeypatch.setattr("app.services.analysis_service.analyze_package", _fake_analyze_package)

    response = client.post(
        "/api/packages/analyze",
        json={
            "name": "urllib3",
            "version": "1!2.0.0.post1",
            "registry": "pypi",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["package"]["registry"] == "pypi"
    assert body["package"]["version"] == "1!2.0.0.post1"


def test_analyze_rejects_non_semver_npm_version(client):
    response = client.post(
        "/api/packages/analyze",
        json={
            "name": "left-pad",
            "version": "1.2",
            "registry": "npm",
        },
    )

    assert response.status_code == 422


def test_analyze_rejects_pypi_range_specifier(client):
    response = client.post(
        "/api/packages/analyze",
        json={
            "name": "requests",
            "version": ">=2.31.0",
            "registry": "pypi",
        },
    )

    assert response.status_code == 422
