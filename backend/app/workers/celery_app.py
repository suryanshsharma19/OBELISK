"""Celery application instance.

Configures the Celery broker (Redis) and result backend.
Workers import this module to get the app instance.

Usage:
    celery -A app.workers.celery_app worker --loglevel=info
"""

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "obelisk",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,           # 10 minutes hard limit
    task_soft_time_limit=540,      # 9 minutes soft limit
    worker_prefetch_multiplier=1,  # fair scheduling
)

# Auto-discover tasks in the workers module
celery_app.autodiscover_tasks(["app.workers"])
