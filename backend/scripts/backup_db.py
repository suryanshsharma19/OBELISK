#!/usr/bin/env python3
"""
Database backup utility.

Dumps the PostgreSQL database to a timestamped SQL file using pg_dump.
Keeps the last 7 backups and deletes older ones.

Usage:
    python -m scripts.backup_db
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.core.logging import setup_logger

logger = setup_logger("backup_db")
settings = get_settings()

BACKUP_DIR = Path("backups")
MAX_BACKUPS = 7


def run_backup() -> Path:
    """Execute pg_dump and return the path to the backup file."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = BACKUP_DIR / f"obelisk_{timestamp}.sql"

    cmd = [
        "pg_dump",
        "-h", settings.postgres_host,
        "-p", str(settings.postgres_port),
        "-U", settings.postgres_user,
        "-d", settings.postgres_db,
        "-f", str(filename),
        "--no-password",
    ]

    env = {"PGPASSWORD": settings.postgres_password}

    logger.info("Running pg_dump → %s", filename)
    result = subprocess.run(cmd, env={**dict(__import__("os").environ), **env}, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error("pg_dump failed: %s", result.stderr)
        raise RuntimeError(f"pg_dump exited with code {result.returncode}")

    logger.info("Backup created: %s (%.1f KB)", filename, filename.stat().st_size / 1024)
    return filename


def cleanup_old_backups() -> None:
    """Remove backups beyond MAX_BACKUPS, keeping the most recent."""
    backups = sorted(BACKUP_DIR.glob("obelisk_*.sql"), reverse=True)
    for old in backups[MAX_BACKUPS:]:
        old.unlink()
        logger.info("Removed old backup: %s", old.name)


def main() -> None:
    logger.info("Starting database backup …")
    try:
        path = run_backup()
        cleanup_old_backups()
        logger.info("Backup complete: %s", path)
    except Exception as exc:
        logger.error("Backup failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
