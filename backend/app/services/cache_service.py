"""Cache Service — thin business-logic layer over Redis.

Encapsulates key naming conventions and TTL policies so the rest
of the app doesn't need to know about Redis key formats.

Functions:
    get_analysis_cache / set_analysis_cache
    get_stats_cache   / set_stats_cache
    invalidate_package_cache
"""

from __future__ import annotations

from typing import Any, Optional

from app.core.logging import setup_logger

logger = setup_logger(__name__)

# TTL constants (seconds)
ANALYSIS_TTL = 3600      # 1 hour
STATS_TTL = 300           # 5 minutes
PACKAGE_LIST_TTL = 120    # 2 minutes


def _get_client():
    from app.db.redis_client import redis_client
    return redis_client


# ------------------------------------------------------------------
# Analysis cache
# ------------------------------------------------------------------

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


# ------------------------------------------------------------------
# Stats cache
# ------------------------------------------------------------------

def get_stats_cache(key_name: str) -> Optional[dict[str, Any]]:
    return _get_client().get_json(f"stats:{key_name}")


def set_stats_cache(key_name: str, data: dict[str, Any]) -> None:
    _get_client().set_json(f"stats:{key_name}", data, ttl=STATS_TTL)


# ------------------------------------------------------------------
# Package list cache
# ------------------------------------------------------------------

def get_list_cache(key_name: str) -> Optional[dict[str, Any]]:
    return _get_client().get_json(f"list:{key_name}")


def set_list_cache(key_name: str, data: dict[str, Any]) -> None:
    _get_client().set_json(f"list:{key_name}", data, ttl=PACKAGE_LIST_TTL)


# ------------------------------------------------------------------
# Scan counter (tracks daily scan volume)
# ------------------------------------------------------------------

def increment_scan_counter() -> int:
    """Bump the daily scan counter, auto-expires after 24h."""
    from datetime import date
    key = f"scans:{date.today().isoformat()}"
    return _get_client().incr(key, ttl=86400)
