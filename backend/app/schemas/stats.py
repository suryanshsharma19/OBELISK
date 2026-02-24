"""Request/response schemas for /stats endpoints."""

from pydantic import BaseModel, Field


class ThreatDistribution(BaseModel):
    safe: int = 0
    low: int = 0
    medium: int = 0
    high: int = 0
    critical: int = 0


class StatsOverview(BaseModel):
    """Dashboard-level summary stats."""
    total_packages: int = 0
    malicious_packages: int = 0
    active_alerts: int = 0
    scans_24h: int = 0
    threat_distribution: ThreatDistribution = Field(
        default_factory=ThreatDistribution,
    )
    detection_rate: float = 0.0


class TrendDataPoint(BaseModel):
    date: str
    packages_scanned: int = 0
    threats_detected: int = 0


class TrendResponse(BaseModel):
    trend: list[TrendDataPoint] = Field(default_factory=list)
