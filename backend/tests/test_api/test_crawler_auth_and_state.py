"""API tests for crawler auth requirements and state transitions."""


def test_crawler_status_requires_auth(unauth_client):
    resp = unauth_client.get("/api/crawler/status")
    assert resp.status_code == 401


def test_crawler_lifecycle_state_transitions(client):
    started = client.post("/api/crawler/start")
    assert started.status_code == 200
    assert started.json()["status"] in {"started", "already_running"}

    status_running = client.get("/api/crawler/status")
    assert status_running.status_code == 200
    assert status_running.json()["running"] is True

    started_again = client.post("/api/crawler/start")
    assert started_again.status_code == 200
    assert started_again.json()["status"] == "already_running"

    stopped = client.post("/api/crawler/stop")
    assert stopped.status_code == 200
    assert stopped.json()["status"] in {"stopped", "not_running"}

    status_stopped = client.get("/api/crawler/status")
    assert status_stopped.status_code == 200
    assert status_stopped.json()["running"] is False
