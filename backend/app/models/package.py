"""Pydantic models for package data."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


class PackageBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["express"])
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+", examples=["1.0.0"])
    registry: Literal["npm", "pypi"]
    description: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None
    repository_url: Optional[HttpUrl] = None


class PackageCreate(PackageBase):
    pass


class PackageUpdate(BaseModel):
    risk_score: Optional[float] = Field(None, ge=0, le=100)
    threat_level: Optional[Literal["safe", "low", "medium", "high", "critical"]] = None
    is_malicious: Optional[bool] = None


class PackageResponse(PackageBase):
    id: int
    risk_score: float = 0.0
    threat_level: str = "safe"
    is_malicious: bool = False
    analyzed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

