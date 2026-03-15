"""Output formatting utilities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional


def format_analysis_response(
    risk_score: float,
    threat_level: str,
    is_malicious: bool,
    confidence: float,
    breakdown: dict[str, Any],
) -> dict[str, Any]:
    return {
        "risk_score": round(risk_score, 2),
        "threat_level": threat_level,
        "is_malicious": is_malicious,
        "confidence": round(confidence, 3),
        "breakdown": breakdown,
    }


def format_package_summary(pkg: Any) -> dict[str, Any]:
    return {
        "id": pkg.id,
        "name": pkg.name,
        "version": pkg.version,
        "registry": pkg.registry.value if hasattr(pkg.registry, "value") else str(pkg.registry),
        "risk_score": round(pkg.risk_score or 0.0, 2),
        "threat_level": (
            pkg.threat_level.value
            if hasattr(pkg.threat_level, "value")
            else str(pkg.threat_level or "safe")
        ),
        "is_malicious": pkg.is_malicious or False,
        "analyzed_at": _fmt_dt(pkg.analyzed_at),
    }


def format_alert_summary(alert: Any) -> dict[str, Any]:
    return {
        "id": alert.id,
        "title": alert.title,
        "threat_level": (
            alert.threat_level.value
            if hasattr(alert.threat_level, "value")
            else str(alert.threat_level)
        ),
        "is_read": alert.is_read,
        "is_resolved": alert.is_resolved,
        "created_at": _fmt_dt(alert.created_at),
    }


def _fmt_dt(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return dt.isoformat()
