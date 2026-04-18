"""Request/response schemas for /packages endpoints."""

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, computed_field

from app.models.package import PackageResponse
from app.models.package import SEMVER_PATTERN


class AnalyzeRequest(BaseModel):
    name: str = Field(..., examples=["express"])
    version: str = Field(..., pattern=SEMVER_PATTERN, examples=["4.18.0"])
    registry: Literal["npm", "pypi"] = "npm"
    code: Optional[str] = None


class AnalysisBreakdown(BaseModel):
    typosquatting: float = 0.0
    code_analysis: float = 0.0
    behavior: float = 0.0
    maintainer: float = 0.0
    dependency: float = 0.0


class AnalyzeResponse(BaseModel):
    package: PackageResponse
    analysis: dict[str, Any] = Field(
        default_factory=lambda: {
            "risk_score": 0.0,
            "threat_level": "safe",
            "is_malicious": False,
            "confidence": 0.0,
            "breakdown": {},
        }
    )
    detection_details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PackageListResponse(BaseModel):
    packages: list[PackageResponse]
    total: int
    skip: int = 0
    limit: int = 20

    @computed_field
    @property
    def has_more(self) -> bool:
        return self.skip + self.limit < self.total


class PackageDetailResponse(BaseModel):
    package: PackageResponse
    analysis: Optional[dict[str, Any]] = None
    alerts: list[dict[str, Any]] = Field(default_factory=list)

