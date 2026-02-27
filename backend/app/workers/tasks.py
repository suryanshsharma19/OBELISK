"""Celery task definitions for background work.

Tasks:
    analyze_package_task:  Run the analysis pipeline asynchronously
    crawl_registry_task:   Scan the registry for new packages
"""

from app.core.logging import setup_logger
from app.workers.celery_app import celery_app

logger = setup_logger(__name__)


@celery_app.task(bind=True, name="analyze_package", max_retries=3)
def analyze_package_task(self, name: str, version: str, registry: str, code: str | None = None):
    """
    Background task wrapper for analysis_service.analyze_package.

    Using Celery lets us offload heavy analyses from the request
    cycle and retry on transient failures.
    """
    import asyncio
    from app.db.session import SessionLocal
    from app.services.analysis_service import analyze_package

    logger.info("Task: analysing %s@%s (%s)", name, version, registry)

    db = SessionLocal()
    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            analyze_package(name, version, registry, code, db)
        )
        return result
    except Exception as exc:
        logger.error("Task failed for %s@%s: %s", name, version, exc)
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()
        loop.close()


@celery_app.task(name="crawl_registry")
def crawl_registry_task(registry: str = "npm", batch_size: int = 50):
    """
    Scan the registry for recently published packages and queue
    them for analysis.
    """
    logger.info("Crawl task: scanning %s (batch=%d)", registry, batch_size)
    # In production this would hit the registry changes feed,
    # parse new package names, and kick off analyze_package_task
    # for each one.  Stubbed for now.
    return {"registry": registry, "batch_size": batch_size, "status": "completed"}
