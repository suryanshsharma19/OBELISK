"""Observability helpers: request tracing context + Prometheus metrics."""

from __future__ import annotations

from typing import Any

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

from app.config import get_settings
from app.core.logging import setup_logger
from app.core.request_context import get_request_id as _get_request_id
from app.core.request_context import reset_request_id as _reset_request_id
from app.core.request_context import set_request_id as _set_request_id

logger = setup_logger(__name__)
settings = get_settings()

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests handled by the backend.",
    ["method", "path", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of in-flight HTTP requests.",
    ["method", "path"],
)

DETECTOR_DURATION_SECONDS = Histogram(
    "detector_duration_seconds",
    "Detector execution duration in seconds.",
    ["detector"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

DETECTOR_FAILURES_TOTAL = Counter(
    "detector_failures_total",
    "Total detector failures by detector name.",
    ["detector"],
)

ANALYSIS_CACHE_REQUESTS_TOTAL = Counter(
    "analysis_cache_requests_total",
    "Analysis cache outcomes.",
    ["outcome"],  # hit | miss | error
)

CELERY_QUEUE_BACKLOG = Gauge(
    "celery_queue_backlog",
    "Current queue length for Celery queues.",
    ["queue"],
)

WORKER_HEALTH_STATUS = Gauge(
    "worker_health_status",
    "Worker health (1 healthy, 0 unhealthy).",
    ["worker"],
)

CRAWLER_BATCH_QUEUED_TOTAL = Counter(
    "crawler_batch_queued_total",
    "Total packages queued by crawler tasks.",
)

CRAWLER_BATCH_FAILED_TOTAL = Counter(
    "crawler_batch_failed_total",
    "Total packages that failed queueing in crawler tasks.",
)

CRAWLER_DUPLICATES_SKIPPED_TOTAL = Counter(
    "crawler_duplicates_skipped_total",
    "Total duplicate package entries skipped by crawler batching.",
)


def set_request_id(request_id: str):
    return _set_request_id(request_id)


def get_request_id() -> str:
    return _get_request_id()


def reset_request_id(token) -> None:
    _reset_request_id(token)


def observe_http_request(method: str, path: str, status: int, duration_seconds: float) -> None:
    method = (method or "UNKNOWN").upper()
    path = path or "/"
    status_label = str(status)

    HTTP_REQUESTS_TOTAL.labels(method, path, status_label).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(method, path).observe(duration_seconds)


def observe_detector(detector: str, duration_seconds: float, failed: bool) -> None:
    detector_name = detector or "unknown"
    DETECTOR_DURATION_SECONDS.labels(detector_name).observe(max(duration_seconds, 0.0))
    if failed:
        DETECTOR_FAILURES_TOTAL.labels(detector_name).inc()


def mark_analysis_cache_hit() -> None:
    ANALYSIS_CACHE_REQUESTS_TOTAL.labels("hit").inc()


def mark_analysis_cache_miss() -> None:
    ANALYSIS_CACHE_REQUESTS_TOTAL.labels("miss").inc()


def mark_analysis_cache_error() -> None:
    ANALYSIS_CACHE_REQUESTS_TOTAL.labels("error").inc()


def record_crawler_batch(queued: int, failed: int, duplicates_skipped: int) -> None:
    if queued > 0:
        CRAWLER_BATCH_QUEUED_TOTAL.inc(queued)
    if failed > 0:
        CRAWLER_BATCH_FAILED_TOTAL.inc(failed)
    if duplicates_skipped > 0:
        CRAWLER_DUPLICATES_SKIPPED_TOTAL.inc(duplicates_skipped)


def _safe_redis_queue_depth(queue_name: str = "celery") -> int:
    from app.db.redis_client import redis_client

    try:
        depth = int(redis_client.client.llen(queue_name))
        CELERY_QUEUE_BACKLOG.labels(queue_name).set(depth)
        return depth
    except Exception as exc:
        logger.warning("Failed to read Celery queue depth from Redis: %s", exc)
        CELERY_QUEUE_BACKLOG.labels(queue_name).set(0)
        return 0


def _safe_worker_ping() -> dict[str, Any]:
    from app.workers.celery_app import celery_app

    try:
        inspector = celery_app.control.inspect(timeout=settings.worker_health_check_timeout_s)
        response = inspector.ping() or {}
        healthy = bool(response)
        WORKER_HEALTH_STATUS.labels("celery").set(1 if healthy else 0)
        return {
            "healthy": healthy,
            "workers": sorted(response.keys()),
        }
    except Exception as exc:
        logger.warning("Celery worker health check failed: %s", exc)
        WORKER_HEALTH_STATUS.labels("celery").set(0)
        return {
            "healthy": False,
            "workers": [],
            "error": str(exc),
        }


def collect_worker_observability() -> dict[str, Any]:
    worker = _safe_worker_ping()
    queue_depth = _safe_redis_queue_depth("celery")

    return {
        "worker": worker,
        "queue": {
            "name": "celery",
            "depth": queue_depth,
        },
    }


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
