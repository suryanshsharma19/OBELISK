"""Pydantic models for package data."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

SEMVER_PATTERN = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"


class PackageBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["express"])
    version: str = Field(..., pattern=SEMVER_PATTERN, examples=["1.0.0"])
    registry: Literal["npm", "pypi"]
    description: Optional[str] = Field(default=None, max_length=2000)
    author: Optional[str] = Field(default=None, max_length=255)
    license: Optional[str] = Field(default=None, max_length=100)
    repository_url: Optional[HttpUrl] = None

    @field_validator("name")
    @classmethod
    def _normalize_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("version")
    @classmethod
    def _normalize_version(cls, value: str) -> str:
        return value.strip()


class PackageCreate(PackageBase):
    model_config = ConfigDict(extra="forbid")


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

    model_config = ConfigDict(from_attributes=True)

