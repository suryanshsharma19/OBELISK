"""Request/response schemas for /alerts endpoints."""

from typing import Optional

from pydantic import BaseModel, Field

from app.models.alert import AlertResponse


class AlertListResponse(BaseModel):
    """Paginated alert list response."""
    alerts: list[AlertResponse]
    total: int
    skip: int = 0
    limit: int = 20
    unread_count: int = 0


class AlertActionRequest(BaseModel):
    """Bulk-action request for multiple alerts."""
    alert_ids: list[int] = Field(..., min_length=1)
    action: str = Field(..., pattern="^(mark_read|resolve|report)$")


class AlertActionResponse(BaseModel):
    updated: int = 0
    message: str = "OK"
