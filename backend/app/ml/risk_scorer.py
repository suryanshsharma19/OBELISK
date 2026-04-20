"""Risk scorer - combines all detector outputs into a final threat assessment."""

from __future__ import annotations

import os
from typing import Any

from app.core.logging import setup_logger
from app.models.analysis import AnalysisResult, DetectionResult
from app.utils.constants import DETECTION_WEIGHTS
from app.utils.helpers import calculate_threat_level, get_current_timestamp

logger = setup_logger(__name__)

# score above which a detector "agrees" the package is suspicious
AGREEMENT_THRESHOLD = 50.0

MALICIOUS_THRESHOLD = 60.0

# Code analysis can over-score benign snippets in isolation.
# If no other detector crosses agreement threshold, dampen the aggregate.
CODE_ONLY_DAMPENING_FACTOR = 0.65


class RiskScorer:
    """Aggregate individual detection scores into a final risk assessment."""

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or DETECTION_WEIGHTS

    def calculate_risk(
        self,
        detection_results: dict[str, DetectionResult],
    ) -> AnalysisResult:
        # weighted sum
        weighted_score = 0.0
        contributions: dict[str, dict[str, Any]] = {}

        for name, weight in self.weights.items():
            result = detection_results.get(name)
            if result is None:
                contributions[name] = {
                    "score": 0.0,
                    "weight": weight,
                    "contribution": 0.0,
                }
                continue

            contribution = result.score * weight
            weighted_score += contribution
            contributions[name] = {
                "score": round(result.score, 2),
                "weight": weight,
                "contribution": round(contribution, 2),
            }

        risk_score = round(min(weighted_score, 100.0), 2)
        risk_score, calibration = self._apply_calibration(risk_score, detection_results)
        threat_level = calculate_threat_level(risk_score)
        is_malicious = risk_score >= MALICIOUS_THRESHOLD

        # confidence based on detector agreement
        confidence = self._calculate_confidence(detection_results)

        logger.info(
            "Risk score calculated: %.2f (%s) malicious=%s confidence=%.2f",
            risk_score, threat_level, is_malicious, confidence,
        )

        return AnalysisResult(
            risk_score=risk_score,
            threat_level=threat_level,
            is_malicious=is_malicious,
            confidence=confidence,
            detection_details={
                "breakdown": contributions,
                "weights_used": self.weights,
                "agreement_threshold": AGREEMENT_THRESHOLD,
                "malicious_threshold": MALICIOUS_THRESHOLD,
                "calibration": calibration,
            },
            analyzed_at=get_current_timestamp(),
        )

    def _apply_calibration(
        self,
        risk_score: float,
        detection_results: dict[str, DetectionResult],
    ) -> tuple[float, dict[str, Any]]:
        if os.getenv("RISK_DISABLE_CALIBRATION", "false").strip().lower() in {"1", "true", "yes"}:
            return round(risk_score, 2), {
                "applied": False,
                "policy": "disabled_by_env",
                "pre_calibration_risk": round(risk_score, 2),
                "post_calibration_risk": round(risk_score, 2),
            }

        code_result = detection_results.get("code_analysis")
        other_detector_high = any(
            (name != "code_analysis") and result is not None and result.score > AGREEMENT_THRESHOLD
            for name, result in detection_results.items()
        )

        calibration = {
            "applied": False,
            "policy": "none",
            "pre_calibration_risk": round(risk_score, 2),
            "post_calibration_risk": round(risk_score, 2),
        }

        if code_result is None:
            return round(risk_score, 2), calibration

        if code_result.score > AGREEMENT_THRESHOLD and not other_detector_high:
            adjusted = round(risk_score * CODE_ONLY_DAMPENING_FACTOR, 2)
            calibration.update(
                {
                    "applied": True,
                    "policy": "code_analysis_only_dampening",
                    "factor": CODE_ONLY_DAMPENING_FACTOR,
                    "post_calibration_risk": adjusted,
                }
            )
            return adjusted, calibration

        return round(risk_score, 2), calibration

    def _calculate_confidence(
        self,
        detection_results: dict[str, DetectionResult],
    ) -> float:
        if not detection_results:
            return 0.0

        active = [r for r in detection_results.values() if r is not None]
        if not active:
            return 0.0

        agreements = sum(
            1 for r in active if r.score > AGREEMENT_THRESHOLD
        )
        all_below = all(r.score <= AGREEMENT_THRESHOLD for r in active)

        # If everything is below threshold, that's high confidence in "safe"
        if all_below:
            return round(1.0 - max(r.score for r in active) / 100, 2)

        return round(agreements / len(active), 2)
