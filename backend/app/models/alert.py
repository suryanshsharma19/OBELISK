"""Pydantic models for alert data."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class AlertBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    threat_level: Literal["low", "medium", "high", "critical"] = "medium"


class AlertCreate(AlertBase):
    """Payload for creating a new alert."""
    package_id: int


class AlertUpdate(BaseModel):
    """Partial update — mark read, resolved, etc."""
    is_read: Optional[bool] = None
    is_resolved: Optional[bool] = None
    registry_reported: Optional[bool] = None
    blocked_in_ci: Optional[bool] = None


class AlertResponse(AlertBase):
    """Alert as it gets returned from the API."""
    id: int
    package_id: int
    is_read: bool = False
    is_resolved: bool = False
    registry_reported: bool = False
    blocked_in_ci: bool = False
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True
