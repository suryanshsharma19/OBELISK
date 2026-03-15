#!/usr/bin/env python3
"""Health check script - verifies all services are reachable."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from app.config import get_settings
from app.core.logging import setup_logger

logger = setup_logger("health_check")
settings = get_settings()


def check_postgres() -> bool:
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(settings.postgres_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("  ✓  PostgreSQL — OK")
        return True
    except Exception as exc:
        logger.error("  ✗  PostgreSQL — %s", exc)
        return False


def check_redis() -> bool:
    try:
        import redis as redis_lib
        r = redis_lib.Redis(host=settings.redis_host, port=settings.redis_port, socket_timeout=3)
        r.ping()
        logger.info("  ✓  Redis — OK")
        return True
    except Exception as exc:
        logger.error("  ✗  Redis — %s", exc)
        return False


def check_neo4j() -> bool:
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        driver.verify_connectivity()
        driver.close()
        logger.info("  ✓  Neo4j — OK")
        return True
    except Exception as exc:
        logger.error("  ✗  Neo4j — %s", exc)
        return False


def check_backend() -> bool:
    url = f"http://{settings.api_host}:{settings.api_port}/health"
    try:
        resp = httpx.get(url, timeout=5)
        if resp.status_code == 200:
            logger.info("  ✓  Backend API — OK")
            return True
        logger.error("  ✗  Backend API — HTTP %d", resp.status_code)
        return False
    except Exception as exc:
        logger.error("  ✗  Backend API — %s", exc)
        return False


def main() -> None:
    logger.info("Running OBELISK health checks …")
    results = [
        check_postgres(),
        check_redis(),
        check_neo4j(),
        check_backend(),
    ]
    passed = sum(results)
    total = len(results)

    if all(results):
        logger.info("All %d checks passed ✓", total)
        sys.exit(0)
    else:
        logger.warning("%d/%d checks passed", passed, total)
        sys.exit(1)


if __name__ == "__main__":
    main()
