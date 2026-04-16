"""Reliability tests for worker tasks: retries, failures, backlog, idempotency."""

from __future__ import annotations

import pytest

from app.workers import tasks


class _DummyDbSession:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_analyze_task_retries_on_pipeline_failure(monkeypatch):
    """analyze_package task should retry with countdown when analysis fails."""

    dummy_db = _DummyDbSession()
    monkeypatch.setattr("app.db.session.SessionLocal", lambda: dummy_db)

    async def _boom(*args, **kwargs):
        raise RuntimeError("detector pipeline blew up")

    monkeypatch.setattr("app.services.analysis_service.analyze_package", _boom)

    retry_calls: dict[str, object] = {}

    def _fake_retry(*, exc, countdown):
        retry_calls["exc"] = exc
        retry_calls["countdown"] = countdown
        raise RuntimeError("retry-invoked")

    monkeypatch.setattr(tasks.analyze_package_task, "retry", _fake_retry)

    with pytest.raises(RuntimeError, match="retry-invoked"):
        tasks.analyze_package_task.run("example-pkg", "1.2.3", "npm")

    assert isinstance(retry_calls.get("exc"), RuntimeError)
    assert retry_calls.get("countdown") == 30
    assert dummy_db.closed is True


def test_crawl_registry_skips_duplicates_and_records_batch_metrics(monkeypatch):
    """crawl task should queue each unique package once and expose duplicate count."""

    monkeypatch.setattr(
        tasks,
        "_fetch_recent_npm_packages",
        lambda limit: [
            {"name": "alpha", "version": "1.0.0"},
            {"name": "alpha", "version": "1.0.0"},
            {"name": "beta", "version": "2.0.0"},
        ],
    )

    queued_calls: list[tuple[str, str, str]] = []

    def _fake_delay(*, name, version, registry):
        queued_calls.append((name, version, registry))

    monkeypatch.setattr(tasks.analyze_package_task, "delay", _fake_delay)

    metric_payload: dict[str, int] = {}

    def _record_batch(*, queued, failed, duplicates_skipped):
        metric_payload["queued"] = queued
        metric_payload["failed"] = failed
        metric_payload["duplicates_skipped"] = duplicates_skipped

    monkeypatch.setattr(tasks, "record_crawler_batch", _record_batch)

    result = tasks.crawl_registry_task(registry="npm", batch_size=10)

    assert result["status"] == "completed"
    assert result["queued"] == 2
    assert result["failed"] == 0
    assert result["duplicates_skipped"] == 1
    assert queued_calls == [
        ("alpha", "1.0.0", "npm"),
        ("beta", "2.0.0", "npm"),
    ]
    assert metric_payload == {
        "queued": 2,
        "failed": 0,
        "duplicates_skipped": 1,
    }


def test_crawl_registry_reports_queue_failures(monkeypatch):
    """crawl task should continue processing and report failures when queueing fails."""

    monkeypatch.setattr(
        tasks,
        "_fetch_recent_npm_packages",
        lambda limit: [
            {"name": "ok-pkg", "version": "1.0.0"},
            {"name": "bad-pkg", "version": "3.0.0"},
        ],
    )

    def _fake_delay(*, name, version, registry):
        if name == "bad-pkg":
            raise RuntimeError("broker unavailable")

    monkeypatch.setattr(tasks.analyze_package_task, "delay", _fake_delay)

    metric_payload: dict[str, int] = {}

    def _record_batch(*, queued, failed, duplicates_skipped):
        metric_payload["queued"] = queued
        metric_payload["failed"] = failed
        metric_payload["duplicates_skipped"] = duplicates_skipped

    monkeypatch.setattr(tasks, "record_crawler_batch", _record_batch)

    result = tasks.crawl_registry_task(registry="npm", batch_size=10)

    assert result["status"] == "completed"
    assert result["queued"] == 1
    assert result["failed"] == 1
    assert result["duplicates_skipped"] == 0
    assert result["failures"]
    assert result["failures"][0]["name"] == "bad-pkg"

    assert metric_payload == {
        "queued": 1,
        "failed": 1,
        "duplicates_skipped": 0,
    }
