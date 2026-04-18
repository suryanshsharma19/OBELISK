"""Celery task definitions for background work."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.config import get_settings
from app.core.logging import setup_logger
from app.core.observability import record_crawler_batch
from app.workers.celery_app import celery_app

logger = setup_logger(__name__)
settings = get_settings()


@celery_app.task(bind=True, name="analyze_package", max_retries=3)
def analyze_package_task(self, name: str, version: str, registry: str, code: str | None = None):
    from app.db.session import SessionLocal
    from app.services.analysis_service import analyze_package

    logger.info("Task: analysing %s@%s (%s)", name, version, registry)

    db = SessionLocal()
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(analyze_package(name, version, registry, code, db))
        return result
    except Exception as exc:
        logger.error("Task failed for %s@%s: %s", name, version, exc)
        raise self.retry(exc=exc, countdown=30) from exc
    finally:
        db.close()
        loop.close()


@celery_app.task(name="crawl_registry")
def crawl_registry_task(registry: str = "npm", batch_size: int = 50):
    logger.info("Crawl task: scanning %s (batch=%d)", registry, batch_size)

    try:
        if registry == "npm":
            candidates = _fetch_recent_npm_packages(batch_size)
        elif registry == "pypi":
            candidates = _fetch_recent_pypi_packages(batch_size)
        else:
            return {
                "registry": registry,
                "batch_size": batch_size,
                "status": "failed",
                "error": f"Unsupported registry: {registry}",
                "queued": 0,
                "candidates": 0,
                "threats_found": 0,
            }
    except Exception as exc:
        logger.error("Registry crawl failed for %s: %s", registry, exc)
        return {
            "registry": registry,
            "batch_size": batch_size,
            "status": "failed",
            "error": str(exc),
            "queued": 0,
            "candidates": 0,
            "threats_found": 0,
        }

    queued = 0
    duplicates_skipped = 0
    failures: list[dict[str, str]] = []
    seen_keys: set[tuple[str, str]] = set()
    candidate_count = len(candidates)

    for package in candidates:
        name = package.get("name")
        version = package.get("version") or "0.0.0"
        if not name:
            continue

        dedupe_key = (name, version)
        if dedupe_key in seen_keys:
            duplicates_skipped += 1
            continue
        seen_keys.add(dedupe_key)

        try:
            analyze_package_task.delay(name=name, version=version, registry=registry)
            queued += 1
        except Exception as exc:
            failures.append({"name": name, "error": str(exc)})

    record_crawler_batch(
        queued=queued,
        failed=len(failures),
        duplicates_skipped=duplicates_skipped,
    )

    logger.info(
        "Crawl complete for %s. queued=%d failed=%d",
        registry,
        queued,
        len(failures),
    )

    return {
        "registry": registry,
        "batch_size": batch_size,
        "status": "completed",
        "candidates": candidate_count,
        "queued": queued,
        "failed": len(failures),
        "duplicates_skipped": duplicates_skipped,
        "threats_found": 0,
        "failures": failures[:10],
    }


def _fetch_recent_npm_packages(limit: int) -> list[dict[str, str]]:
    query = "keywords:security OR keywords:utility"
    url = f"{settings.npm_registry_url.rstrip('/')}/-/v1/search"
    params = {"text": query, "size": max(1, min(limit, 250))}

    with httpx.Client(timeout=15.0) as client:
        response = client.get(url, params=params)
        response.raise_for_status()

    payload = response.json()
    objects = payload.get("objects", []) if isinstance(payload, dict) else []
    packages: list[dict[str, str]] = []

    for item in objects:
        pkg = item.get("package", {}) if isinstance(item, dict) else {}
        name = pkg.get("name")
        version = pkg.get("version", "0.0.0")
        if name:
            packages.append({"name": name, "version": version})

    return packages


def _fetch_recent_pypi_packages(limit: int) -> list[dict[str, str]]:
    # PyPI has no "latest changes" API without extra infrastructure,
    # so we sample from a lightweight package index list.
    index_url = "https://pypi.org/simple/"
    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        response = client.get(index_url)
        response.raise_for_status()

    names: list[str] = []
    for line in response.text.splitlines():
        if ">" not in line or "</a>" not in line:
            continue
        start = line.find(">") + 1
        end = line.find("</a>")
        name = line[start:end].strip()
        if name:
            names.append(name)
        if len(names) >= max(1, min(limit, 200)):
            break

    return [{"name": n, "version": "0.0.0"} for n in names]
