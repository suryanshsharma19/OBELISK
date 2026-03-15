"""Alert management routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.logging import setup_logger
from app.services import alert_service
from app.utils.formatters import format_alert_summary

logger = setup_logger(__name__)

router = APIRouter()


@router.get("/")
async def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    threat_level: Optional[str] = Query(None),
    is_resolved: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """Return a paginated list of alerts."""
    alerts, total = alert_service.get_alerts(
        db,
        skip=skip,
        limit=limit,
        threat_level=threat_level,
        is_resolved=is_resolved,
    )
    unread = alert_service.get_unread_count(db)

    return {
        "alerts": [format_alert_summary(a) for a in alerts],
        "total": total,
        "skip": skip,
        "limit": limit,
        "unread_count": unread,
    }


@router.get("/{alert_id}")
async def get_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = alert_service.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {
        "id": alert.id,
        "package_id": alert.package_id,
        "title": alert.title,
        "description": alert.description,
        "threat_level": alert.threat_level.value if hasattr(alert.threat_level, "value") else str(alert.threat_level),
        "is_read": alert.is_read,
        "is_resolved": alert.is_resolved,
        "registry_reported": alert.registry_reported,
        "blocked_in_ci": alert.blocked_in_ci,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
    }


@router.put("/{alert_id}")
async def update_alert(
    alert_id: int,
    is_read: Optional[bool] = None,
    is_resolved: Optional[bool] = None,
    registry_reported: Optional[bool] = None,
    blocked_in_ci: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    alert = alert_service.update_alert(
        db, alert_id,
        is_read=is_read,
        is_resolved=is_resolved,
        registry_reported=registry_reported,
        blocked_in_ci=blocked_in_ci,
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {"message": "Alert updated", "alert_id": alert_id}


@router.post("/bulk")
async def bulk_alert_action(
    alert_ids: list[int],
    action: str = Query(..., pattern="^(mark_read|resolve|report)$"),
    db: Session = Depends(get_db),
):
    if not alert_ids:
        raise HTTPException(status_code=400, detail="No alert IDs provided")

    updated = alert_service.bulk_action(db, alert_ids, action)
    return {"updated": updated, "action": action}
