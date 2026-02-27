#!/usr/bin/env python3
"""
Initialise the OBELISK database.

Creates all tables defined in the ORM if they don't already exist.
Intended to be run once during first deployment or local setup.

Usage:
    python -m scripts.init_db
"""

import sys
from pathlib import Path

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.core.logging import setup_logger
from app.db.base import Base
from app.db.session import engine

# Import all models so they register with Base.metadata
from app.db import models  # noqa: F401

logger = setup_logger("init_db")


def init_database() -> None:
    """Create all tables and print confirmation."""
    settings = get_settings()
    logger.info("Connecting to PostgreSQL at %s:%d/%s",
                settings.postgres_host, settings.postgres_port, settings.postgres_db)

    Base.metadata.create_all(bind=engine)
    logger.info("All tables created successfully")

    # List what we created
    for table_name in Base.metadata.tables:
        logger.info("  ✓ %s", table_name)


if __name__ == "__main__":
    init_database()
