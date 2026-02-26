"""
Risk Scorer — combines all detector outputs into a single threat assessment.

The final risk score is a weighted average of the five detectors:
  - Typosquatting:   25%
  - Code Analysis:   35%
  - Behavior:        15%
  - Maintainer:      15%
  - Dependency:      10%

Confidence is derived from detector agreement: the more detectors
that agree on "suspicious" (score > 50), the higher the confidence.

Classes:
    RiskScorer

Usage:
    scorer = RiskScorer()
    result = scorer.calculate_risk({
        "typosquatting": DetectionResult(score=97.3, ...),
        "code_analysis": DetectionResult(score=85.0, ...),
        ...
    })
"""

from __future__ import annotations

from typing import Any

from app.core.logging import setup_logger
from app.models.analysis import AnalysisResult, DetectionResult
from app.utils.constants import DETECTION_WEIGHTS
from app.utils.helpers import calculate_threat_level, get_current_timestamp

logger = setup_logger(__name__)

# Score above which a detector "agrees" that the package is suspicious
AGREEMENT_THRESHOLD = 50.0

# Risk score above which we flag the package as malicious
MALICIOUS_THRESHOLD = 60.0


class RiskScorer:
    """Aggregate individual detection scores into a final risk assessment."""

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or DETECTION_WEIGHTS

    def calculate_risk(
        self,
        detection_results: dict[str, DetectionResult],
    ) -> AnalysisResult:
        """
        Compute the weighted risk score from all detector outputs.

        Args:
            detection_results: Mapping of detector_name → DetectionResult.

        Returns:
            AnalysisResult with combined score, threat level, confidence.
        """
        # Weighted sum
        weighted_score = 0.0
        contributions: dict[str, dict[str, Any]] = {}

        for name, weight in self.weights.items():
            result = detection_results.get(name)
            if result is None:
                # Detector didn't run — treat as zero
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
        threat_level = calculate_threat_level(risk_score)
        is_malicious = risk_score >= MALICIOUS_THRESHOLD

        # Calculate confidence based on detector agreement
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
            },
            analyzed_at=get_current_timestamp(),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _calculate_confidence(
        self,
        detection_results: dict[str, DetectionResult],
    ) -> float:
        """
        Confidence = proportion of active detectors agreeing on
        'suspicious' (score > AGREEMENT_THRESHOLD).
        """
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
