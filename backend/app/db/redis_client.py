"""Redis client wrapper for caching."""

from __future__ import annotations

import json
from typing import Any, Optional

import redis

from app.config import get_settings
from app.core.exceptions import DatabaseError
from app.core.logging import setup_logger

logger = setup_logger(__name__)
settings = get_settings()

DEFAULT_TTL = 3600


class RedisClient:
    """Convenience layer over the redis-py client."""

    def __init__(self, url: Optional[str] = None) -> None:
        self._url = url or settings.redis_url
        self._client: Optional[redis.Redis] = None

    def connect(self) -> None:
        if self._client is not None:
            return
        try:
            self._client = redis.from_url(
                self._url,
                decode_responses=True,  # always get str back, not bytes
            )
            self._client.ping()
            logger.info("Connected to Redis at %s", self._url)
        except Exception as exc:
            logger.error("Redis connection failed: %s", exc)
            raise DatabaseError(
                "Could not connect to Redis",
                details={"url": self._url, "error": str(exc)},
            ) from exc

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Redis connection closed")

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self.connect()
        return self._client

    def set_json(
        self, key: str, value: Any, ttl: int = DEFAULT_TTL,
    ) -> None:
        try:
            payload = json.dumps(value, default=str)
            self.client.setex(key, ttl, payload)
        except Exception as exc:
            logger.warning("Redis SET failed for key=%s: %s", key, exc)

    def get_json(self, key: str) -> Optional[Any]:
        try:
            raw = self.client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as exc:
            logger.warning("Redis GET failed for key=%s: %s", key, exc)
            return None

    def set(self, key: str, value: str, ttl: int = DEFAULT_TTL) -> None:
        try:
            self.client.setex(key, ttl, value)
        except Exception as exc:
            logger.warning("Redis SET failed for key=%s: %s", key, exc)

    def get(self, key: str) -> Optional[str]:
        try:
            return self.client.get(key)
        except Exception as exc:
            logger.warning("Redis GET failed for key=%s: %s", key, exc)
            return None

    def delete(self, key: str) -> None:
        try:
            self.client.delete(key)
        except Exception as exc:
            logger.warning("Redis DELETE failed for key=%s: %s", key, exc)

    def exists(self, key: str) -> bool:
        try:
            return bool(self.client.exists(key))
        except Exception:
            return False

    def incr(self, key: str, ttl: Optional[int] = None) -> int:
        try:
            val = self.client.incr(key)
            if ttl and val == 1:
                self.client.expire(key, ttl)
            return val
        except Exception as exc:
            logger.warning("Redis INCR failed for key=%s: %s", key, exc)
            return 0

    def flush_all(self) -> None:
        self.client.flushall()
        logger.warning("Redis FLUSHALL executed")


redis_client = RedisClient()
