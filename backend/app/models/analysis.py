"""Pydantic models for analysis data (not SQLAlchemy ORM models)."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class DetectionResult(BaseModel):
    """Output from a single ML detector."""
    score: float = Field(0.0, ge=0, le=100, description="Threat score 0-100")
    confidence: float = Field(0.0, ge=0, le=1.0)
    evidence: dict[str, Any] = Field(default_factory=dict)
    detector_name: str = ""
    execution_time_ms: float = 0.0


class AnalysisBreakdown(BaseModel):
    """Per-detector score breakdown with weighted contributions."""
    typosquatting: DetectionResult = Field(default_factory=DetectionResult)
    code_analysis: DetectionResult = Field(default_factory=DetectionResult)
    behavior: DetectionResult = Field(default_factory=DetectionResult)
    maintainer: DetectionResult = Field(default_factory=DetectionResult)
    dependency: DetectionResult = Field(default_factory=DetectionResult)


class AnalysisResult(BaseModel):
    """Complete analysis output returned to the API layer."""
    risk_score: float = Field(0.0, ge=0, le=100)
    threat_level: str = "safe"
    is_malicious: bool = False
    confidence: float = Field(0.0, ge=0, le=1.0)
    breakdown: AnalysisBreakdown = Field(default_factory=AnalysisBreakdown)
    detection_details: dict[str, Any] = Field(default_factory=dict)
    analyzed_at: Optional[datetime] = None


class AnalysisCreate(BaseModel):
    """Fields needed to persist analysis to the DB."""
    package_id: int
    typosquatting_score: float = 0.0
    code_analysis_score: float = 0.0
    behavior_score: float = 0.0
    maintainer_score: float = 0.0
    dependency_score: float = 0.0
    typosquatting_evidence: Optional[dict[str, Any]] = None
    code_patterns: Optional[dict[str, Any]] = None
    behaviors: Optional[dict[str, Any]] = None
    dependencies: Optional[dict[str, Any]] = None
    maintainer_flags: Optional[dict[str, Any]] = None
    confidence: float = 0.0
