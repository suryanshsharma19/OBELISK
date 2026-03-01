"""Notification service - in-app and external notifications."""

from __future__ import annotations

from typing import Any, Callable

from app.core.logging import setup_logger

logger = setup_logger(__name__)

_subscribers: list[Callable] = []


def subscribe(callback) -> None:
    _subscribers.append(callback)


def _dispatch(event_type: str, payload: dict[str, Any]) -> None:
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
    logger.info(
        "Analysis complete: %s@%s  score=%.1f",
        package_name, version, risk_score,
    )
    _dispatch("analysis_complete", {
        "package": package_name,
        "version": version,
        "risk_score": risk_score,
    })
