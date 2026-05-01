"""Statistics routes - dashboard data endpoints."""

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.logging import setup_logger
from app.db.models import Alert, Package, ThreatLevel

logger = setup_logger(__name__)

router = APIRouter()
from app.ml.actor_clustering import actor_clustering_pipeline
import random

@router.get("/threat-intelligence")
def get_threat_intelligence(db: Session = Depends(get_db)):
    """
    Fetch malicious packages and map them to Threat Actor profiles.
    Returns clustered data suitable for 3D Scatter Plot mapping.
    """
    # Query database for a sample of packages
    packages = db.query(Package).order_by(Package.risk_score.desc()).limit(100).all()
    if not packages:
        # Mock data if db is empty
        packages = []
        for i in range(50):
            packages.append(type("PackageMock", (object,), {
                "id": i, "name": f"evil-pkg-{i}", "risk_score": random.randint(50, 100), "threat_level": "critical",
                "code_analysis_score": random.random(),
                "network_connections": [1]*random.randint(0, 10),
                "filesystem_targets": [1]*random.randint(0, 10),
            })())

    pkg_dicts = []
    for p in packages:
        pkg_dict = {
            "name": getattr(p, "name", f"mock-{random.randint(1,100)}"),
            "risk_score": getattr(p, "risk_score", 85),
            "threat_level": getattr(p, "threat_level", "critical"),
            "code_analysis_score": getattr(p, "code_analysis_score", random.random()),
            "network_connections": getattr(p, "network_connections", [1]*random.randint(0, 10)),
            "filesystem_targets": getattr(p, "filesystem_targets", [1]*random.randint(0, 10))
        }
        pkg_dicts.append(pkg_dict)

    clustered = actor_clustering_pipeline.cluster_packages(pkg_dicts)
    return clustered


@router.get("/overview")
async def stats_overview(
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    total_packages = db.query(func.count(Package.id)).scalar() or 0
    malicious_packages = (
        db.query(func.count(Package.id))
        .filter(Package.is_malicious == True)
        .scalar()
    ) or 0

    active_alerts = (
        db.query(func.count(Alert.id))
        .filter(Alert.is_resolved == False)
        .scalar()
    ) or 0

    # Packages analysed in the last 24 hours
    since_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    scans_24h = (
        db.query(func.count(Package.id))
        .filter(Package.analyzed_at >= since_24h)
        .scalar()
    ) or 0

    # threat-level breakdown
    distribution = {"safe": 0, "low": 0, "medium": 0, "high": 0, "critical": 0}
    rows = (
        db.query(Package.threat_level, func.count(Package.id))
        .group_by(Package.threat_level)
        .all()
    )
    for level, count in rows:
        key = level.value if hasattr(level, "value") else str(level)
        if key in distribution:
            distribution[key] = count

    detection_rate = round(
        (malicious_packages / total_packages * 100) if total_packages else 0.0, 2,
    )

    return {
        "total_packages": total_packages,
        "malicious_packages": malicious_packages,
        "active_alerts": active_alerts,
        "scans_24h": scans_24h,
        "threat_distribution": distribution,
        "detection_rate": detection_rate,
    }


@router.get("/trend")
async def stats_trend(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    trend = []
    today = date.today()

    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time()).replace(tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)

        scanned = (
            db.query(func.count(Package.id))
            .filter(Package.analyzed_at >= day_start, Package.analyzed_at < day_end)
            .scalar()
        ) or 0

        threats = (
            db.query(func.count(Package.id))
            .filter(
                Package.analyzed_at >= day_start,
                Package.analyzed_at < day_end,
                Package.is_malicious == True,
            )
            .scalar()
        ) or 0

        trend.append({
            "date": day.isoformat(),
            "total_scans": scanned,
            "packages_scanned": scanned,
            "threats_detected": threats,
        })

    return {"trend": trend}
