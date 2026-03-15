"""Cache service - thin business-logic layer over Redis."""

from __future__ import annotations

from typing import Any, Optional

from app.core.logging import setup_logger

logger = setup_logger(__name__)

ANALYSIS_TTL = 3600      # 1 hour
STATS_TTL = 300           # 5 min
PACKAGE_LIST_TTL = 120    # 2 min


def _get_client():
    from app.db.redis_client import redis_client
    return redis_client


def get_analysis_cache(registry: str, name: str, version: str) -> Optional[dict[str, Any]]:
    key = f"analysis:{registry}:{name}:{version}"
    return _get_client().get_json(key)


def set_analysis_cache(registry: str, name: str, version: str, data: dict[str, Any]) -> None:
    key = f"analysis:{registry}:{name}:{version}"
    _get_client().set_json(key, data, ttl=ANALYSIS_TTL)


def invalidate_package_cache(registry: str, name: str, version: str) -> None:
    key = f"analysis:{registry}:{name}:{version}"
    _get_client().delete(key)
    logger.debug("Invalidated cache for %s", key)


def get_stats_cache(key_name: str) -> Optional[dict[str, Any]]:
    return _get_client().get_json(f"stats:{key_name}")


def set_stats_cache(key_name: str, data: dict[str, Any]) -> None:
    _get_client().set_json(f"stats:{key_name}", data, ttl=STATS_TTL)


def get_list_cache(key_name: str) -> Optional[dict[str, Any]]:
    return _get_client().get_json(f"list:{key_name}")


def set_list_cache(key_name: str, data: dict[str, Any]) -> None:
    _get_client().set_json(f"list:{key_name}", data, ttl=PACKAGE_LIST_TTL)


def increment_scan_counter() -> int:
    from datetime import date
    key = f"scans:{date.today().isoformat()}"
    return _get_client().incr(key, ttl=86400)
