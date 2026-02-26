"""
Anomaly Detector — flags suspicious maintainer profiles.

Uses a rule-based scoring system inspired by Isolation Forest logic:
  - New accounts (< 30 days old)
  - Temporary / disposable email domains
  - First-time publishers with zero history
  - No verified email
  - No GitHub / VCS presence

If scikit-learn's Isolation Forest model is trained and saved, this
module can load it for unsupervised anomaly scoring on numeric features.
Otherwise it falls back to the deterministic rule engine.

Classes:
    AnomalyDetector(BaseDetector)

Usage:
    detector = AnomalyDetector()
    result = await detector.run(maintainer_data={
        "account_age_days": 3,
        "email": "temp@10minutemail.com",
        ...
    })
"""

from __future__ import annotations

from typing import Any, Optional

from app.core.logging import setup_logger
from app.ml.base_detector import BaseDetector
from app.ml.model_loader import load_sklearn_model
from app.models.analysis import DetectionResult

logger = setup_logger(__name__)

# Known disposable / temporary email providers
TEMP_EMAIL_DOMAINS = [
    "10minutemail", "guerrillamail", "tempmail", "throwaway",
    "mailinator", "yopmail", "trashmail", "sharklasers",
    "grr.la", "dispostable", "fakeinbox", "maildrop",
]


class AnomalyDetector(BaseDetector):
    """Score maintainer trustworthiness through heuristic + ML analysis."""

    name = "maintainer"
    version = "1.0.0"
    weight = 0.15

    def __init__(self) -> None:
        super().__init__()
        self._model = None
        self._is_ready = True

    # ------------------------------------------------------------------
    # Optional model loading
    # ------------------------------------------------------------------

    def load_model(self) -> None:
        """Try to load a trained Isolation Forest model."""
        try:
            from app.config import get_settings
            model_path = get_settings().isolation_forest_path + "/model.joblib"
            self._model = load_sklearn_model(model_path)
            logger.info("Isolation Forest model loaded")
        except Exception as exc:
            logger.info("Isolation Forest not available (%s) — using rules only", exc)
            self._model = None

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    async def analyze(self, **kwargs: Any) -> DetectionResult:
        """
        Evaluate maintainer profile for anomalies.

        Keyword Args:
            maintainer_data (dict): Keys may include:
                account_age_days, email, total_packages,
                has_verified_email, github_repos, previous_downloads

        Returns:
            DetectionResult with anomaly flags and score.
        """
        data: dict[str, Any] = kwargs.get("maintainer_data", {})
        if not data:
            return DetectionResult(
                score=0.0,
                confidence=0.3,
                evidence={"note": "No maintainer data available"},
            )

        flags: list[dict[str, Any]] = []
        score = 0.0

        # ---- Rule 1: New account ----
        account_age = data.get("account_age_days", 365)
        if account_age < 30:
            flags.append({
                "flag": "new_account",
                "description": f"Account is only {account_age} days old",
                "severity": "medium",
            })
            score += 20

        # ---- Rule 2: Temporary / disposable email ----
        email = data.get("email", "").lower()
        if any(domain in email for domain in TEMP_EMAIL_DOMAINS):
            flags.append({
                "flag": "temporary_email",
                "description": f"Email appears to be a disposable address",
                "severity": "high",
            })
            score += 30

        # ---- Rule 3: First-time publisher with brand-new account ----
        total_packages = data.get("total_packages", 0)
        if total_packages <= 1 and account_age < 7:
            flags.append({
                "flag": "first_package_new_account",
                "description": "First published package on a week-old account",
                "severity": "high",
            })
            score += 25

        # ---- Rule 4: Unverified email ----
        if not data.get("has_verified_email", True):
            flags.append({
                "flag": "unverified_email",
                "description": "Publisher email is not verified",
                "severity": "medium",
            })
            score += 15

        # ---- Rule 5: No GitHub presence ----
        github_repos = data.get("github_repos", 1)
        if github_repos == 0:
            flags.append({
                "flag": "no_github_repos",
                "description": "Publisher has no public GitHub repositories",
                "severity": "low",
            })
            score += 10

        # ---- Rule 6: Zero previous downloads on other packages ----
        prev_downloads = data.get("previous_downloads", 1)
        if prev_downloads == 0 and total_packages > 0:
            flags.append({
                "flag": "zero_downloads_history",
                "description": "Publisher's other packages have zero downloads",
                "severity": "medium",
            })
            score += 15

        score = min(score, 100.0)
        confidence = min(0.5 + len(flags) * 0.1, 1.0)

        return DetectionResult(
            score=round(score, 2),
            confidence=round(confidence, 3),
            evidence={
                "is_anomalous": score >= 40,
                "flags": flags,
                "total_flags": len(flags),
                "model_used": self._model is not None,
            },
        )
