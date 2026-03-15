"""Alert service - CRUD and business logic for security alerts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.logging import setup_logger
from app.db.models import Alert, Package, ThreatLevel

logger = setup_logger(__name__)


def create_alert(
    db: Session,
    package_id: int,
    title: str,
    description: str,
    threat_level: str,
) -> Alert:
    alert = Alert(
        package_id=package_id,
        title=title,
        description=description,
        threat_level=threat_level,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    logger.info("Created alert #%d for package %d", alert.id, package_id)
    return alert


def get_alerts(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    threat_level: Optional[str] = None,
    is_resolved: Optional[bool] = None,
) -> tuple[list[Alert], int]:
    query = db.query(Alert)

    if threat_level:
        query = query.filter(Alert.threat_level == threat_level)
    if is_resolved is not None:
        query = query.filter(Alert.is_resolved == is_resolved)

    total = query.count()
    rows = (
        query
        .order_by(Alert.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rows, total


def get_alert_by_id(db: Session, alert_id: int) -> Optional[Alert]:
    return db.query(Alert).filter(Alert.id == alert_id).first()


def update_alert(
    db: Session,
    alert_id: int,
    is_read: Optional[bool] = None,
    is_resolved: Optional[bool] = None,
    registry_reported: Optional[bool] = None,
    blocked_in_ci: Optional[bool] = None,
) -> Optional[Alert]:
    alert = get_alert_by_id(db, alert_id)
    if alert is None:
        return None

    if is_read is not None:
        alert.is_read = is_read
    if is_resolved is not None:
        alert.is_resolved = is_resolved
        if is_resolved:
            alert.resolved_at = datetime.now(timezone.utc)
    if registry_reported is not None:
        alert.registry_reported = registry_reported
    if blocked_in_ci is not None:
        alert.blocked_in_ci = blocked_in_ci

    db.commit()
    db.refresh(alert)
    return alert


def bulk_action(db: Session, alert_ids: list[int], action: str) -> int:
    """Batch update multiple alerts. Returns affected count."""
    query = db.query(Alert).filter(Alert.id.in_(alert_ids))

    if action == "mark_read":
        count = query.update({Alert.is_read: True}, synchronize_session=False)
    elif action == "resolve":
        count = query.update(
            {Alert.is_resolved: True, Alert.resolved_at: datetime.now(timezone.utc)},
            synchronize_session=False,
        )
    elif action == "report":
        count = query.update({Alert.registry_reported: True}, synchronize_session=False)
    else:
        logger.warning("Unknown bulk action: %s", action)
        return 0

    db.commit()
    logger.info("Bulk %s on %d alerts", action, count)
    return count


def get_unread_count(db: Session) -> int:
    return (
        db.query(func.count(Alert.id))
        .filter(Alert.is_read == False, Alert.is_resolved == False)
        .scalar()
    ) or 0
