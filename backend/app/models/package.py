"""Pydantic models for package data."""

from datetime import datetime
import re
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

SEMVER_PATTERN = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
PYPI_VERSION_PATTERN = r"^[A-Za-z0-9]+(?:[A-Za-z0-9._+!-]*[A-Za-z0-9])?$"


def is_valid_version_for_registry(version: str, registry: str) -> bool:
    value = version.strip()
    if not value:
        return False

    if registry == "npm":
        return bool(re.fullmatch(SEMVER_PATTERN, value))

    if registry == "pypi":
        # Accept exact, normalized PyPI versions (PEP440-style text) while
        # rejecting specifiers/ranges to keep scanning deterministic.
        return bool(re.fullmatch(PYPI_VERSION_PATTERN, value))

    return False


class PackageBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["express"])
    version: str = Field(
        ...,
        min_length=1,
        max_length=128,
        examples=["1.0.0", "2.31.0", "1!2.0.0.post1"],
    )
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

    @model_validator(mode="after")
    def _validate_registry_version(self) -> "PackageBase":
        if not is_valid_version_for_registry(self.version, self.registry):
            if self.registry == "npm":
                raise ValueError("npm versions must be strict semver (for example 1.2.3)")
            raise ValueError("pypi versions must be exact normalized versions (for example 1.2.3 or 1!2.0.0.post1)")
        return self


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

