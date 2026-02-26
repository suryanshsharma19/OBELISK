"""Notification Service — handles in-app and external notifications.

For now this is a simple logger-based notifier.  When email / Slack /
webhook integrations are added, this is the module to extend.

Functions:
    notify_threat_detected: Push a message about a new threat
    notify_analysis_complete: Inform listeners that analysis is done
"""

from __future__ import annotations

from typing import Any

from app.core.logging import setup_logger

logger = setup_logger(__name__)

# In-memory subscriber list (replaced by a proper message bus later)
_subscribers: list[callable] = []


def subscribe(callback) -> None:
    """Register a callback to receive notifications."""
    _subscribers.append(callback)


def _dispatch(event_type: str, payload: dict[str, Any]) -> None:
    """Push event to all registered subscribers."""
    for cb in _subscribers:
        try:
            cb(event_type, payload)
        except Exception as exc:
            logger.warning("Subscriber error: %s", exc)


def notify_threat_detected(
    package_name: str,
    version: str,
    risk_score: float,
    threat_level: str,
) -> None:
    """Called when a package is flagged as high/critical."""
    logger.warning(
        "THREAT DETECTED: %s@%s  score=%.1f  level=%s",
        package_name, version, risk_score, threat_level,
    )
    _dispatch("threat_detected", {
        "package": package_name,
        "version": version,
        "risk_score": risk_score,
        "threat_level": threat_level,
    })


def notify_analysis_complete(
    package_name: str,
    version: str,
    risk_score: float,
) -> None:
    """Called after any analysis finishes (regardless of result)."""
    logger.info(
        "Analysis complete: %s@%s  score=%.1f",
        package_name, version, risk_score,
    )
    _dispatch("analysis_complete", {
        "package": package_name,
        "version": version,
        "risk_score": risk_score,
    })
