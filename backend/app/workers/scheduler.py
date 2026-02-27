"""Celery Beat schedule configuration.

Defines periodic tasks (cron-style) that run on a timer.
Used for continuous registry monitoring and database cleanup.

Usage:
    celery -A app.workers.celery_app beat --loglevel=info
"""

from celery.schedules import crontab

from app.workers.celery_app import celery_app

# Register periodic tasks
celery_app.conf.beat_schedule = {
    # Crawl npm every 15 minutes
    "crawl-npm-registry": {
        "task": "crawl_registry",
        "schedule": crontab(minute="*/15"),
        "args": ("npm", 100),
    },
    # Crawl PyPI every 30 minutes
    "crawl-pypi-registry": {
        "task": "crawl_registry",
        "schedule": crontab(minute="*/30"),
        "args": ("pypi", 50),
    },
}
