#!/usr/bin/env python3
"""
Seed the database with sample packages and analysis records.

Useful for local development and demo purposes.  Run after init_db.

Usage:
    python -m scripts.seed_data
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.logging import setup_logger
from app.db.models import Alert, Analysis, Package
from app.db.session import SessionLocal

logger = setup_logger("seed_data")

# Sample packages to insert
SEED_PACKAGES = [
    {
        "name": "express",
        "version": "4.18.2",
        "registry": "npm",
        "description": "Fast, unopinionated, minimalist web framework for Node.js",
        "author": "TJ Holowaychuk",
        "risk_score": 2.5,
        "threat_level": "safe",
        "is_malicious": False,
    },
    {
        "name": "expresss",
        "version": "1.0.0",
        "registry": "npm",
        "description": "A fast web framework",
        "author": "unknown",
        "risk_score": 87.4,
        "threat_level": "critical",
        "is_malicious": True,
    },
    {
        "name": "lodash",
        "version": "4.17.21",
        "registry": "npm",
        "description": "Lodash modular utilities",
        "author": "John-David Dalton",
        "risk_score": 1.2,
        "threat_level": "safe",
        "is_malicious": False,
    },
    {
        "name": "l0dash",
        "version": "0.1.0",
        "registry": "npm",
        "description": "Utility functions",
        "author": "temp-user",
        "risk_score": 74.9,
        "threat_level": "high",
        "is_malicious": True,
    },
    {
        "name": "requests",
        "version": "2.31.0",
        "registry": "pypi",
        "description": "Python HTTP for Humans",
        "author": "Kenneth Reitz",
        "risk_score": 3.1,
        "threat_level": "safe",
        "is_malicious": False,
    },
    {
        "name": "requestes",
        "version": "1.0.0",
        "registry": "pypi",
        "description": "HTTP library",
        "author": "unknown",
        "risk_score": 92.1,
        "threat_level": "critical",
        "is_malicious": True,
    },
]


def seed() -> None:
    """Insert seed data into the database."""
    db = SessionLocal()
    try:
        # Check if data already exists
        existing = db.query(Package).count()
        if existing > 0:
            logger.info("Database already has %d packages — skipping seed", existing)
            return

        for pkg_data in SEED_PACKAGES:
            pkg = Package(
                name=pkg_data["name"],
                version=pkg_data["version"],
                registry=pkg_data["registry"],
                description=pkg_data["description"],
                author=pkg_data["author"],
                risk_score=pkg_data["risk_score"],
                threat_level=pkg_data["threat_level"],
                is_malicious=pkg_data["is_malicious"],
                analyzed_at=datetime.now(timezone.utc),
            )
            db.add(pkg)
            db.flush()

            # Create a matching analysis record
            analysis = Analysis(
                package_id=pkg.id,
                typosquatting_score=pkg_data["risk_score"] * 0.8 if pkg_data["is_malicious"] else 0.0,
                code_analysis_score=pkg_data["risk_score"] * 0.5 if pkg_data["is_malicious"] else 2.0,
                behavior_score=pkg_data["risk_score"] * 0.3 if pkg_data["is_malicious"] else 0.0,
                maintainer_score=pkg_data["risk_score"] * 0.4 if pkg_data["is_malicious"] else 0.0,
                dependency_score=0.0,
                confidence=0.95 if pkg_data["is_malicious"] else 0.85,
            )
            db.add(analysis)

            # Generate alerts for malicious packages
            if pkg_data["is_malicious"]:
                alert = Alert(
                    package_id=pkg.id,
                    title=f"Threat detected: {pkg_data['name']}@{pkg_data['version']}",
                    description=f"Risk score {pkg_data['risk_score']:.1f} ({pkg_data['threat_level']})",
                    threat_level=pkg_data["threat_level"],
                )
                db.add(alert)

            logger.info("  Seeded: %s@%s (score=%.1f)", pkg_data["name"], pkg_data["version"], pkg_data["risk_score"])

        db.commit()
        logger.info("Seed complete — %d packages inserted", len(SEED_PACKAGES))
    except Exception as exc:
        db.rollback()
        logger.error("Seed failed: %s", exc)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
