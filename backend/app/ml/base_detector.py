"""Abstract base class for all ML detectors.

Every detector in the ML pipeline inherits from BaseDetector and
implements the `analyze()` method.  This pattern lets the analysis
service treat all detectors uniformly.

Classes:
    BaseDetector: abstract parent for typosquat, code_analyzer, etc.

Usage:
    class MyDetector(BaseDetector):
        name = "my_detector"
        async def analyze(self, **kwargs) -> DetectionResult:
            ...
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from app.core.logging import setup_logger
from app.models.analysis import DetectionResult

logger = setup_logger(__name__)


class BaseDetector(ABC):
    """Contract that every detection module must satisfy."""

    # Subclasses should override these
    name: str = "base"
    version: str = "1.0.0"
    weight: float = 0.0  # contribution weight in final risk score

    def __init__(self) -> None:
        self._is_ready = False
        logger.debug("Initialising detector: %s v%s", self.name, self.version)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(self, **kwargs: Any) -> DetectionResult:
        """
        Wrapper around analyze() that adds timing and error handling.
        Callers should use this instead of analyze() directly.
        """
        start = time.perf_counter()
        try:
            result = await self.analyze(**kwargs)
            elapsed_ms = (time.perf_counter() - start) * 1000
            result.detector_name = self.name
            result.execution_time_ms = round(elapsed_ms, 2)
            logger.info(
                "Detector %s finished in %.1fms  score=%.1f",
                self.name, elapsed_ms, result.score,
            )
            return result
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "Detector %s failed after %.1fms: %s",
                self.name, elapsed_ms, exc,
            )
            # Return a zero-score result rather than crashing the pipeline
            return DetectionResult(
                score=0.0,
                confidence=0.0,
                evidence={"error": str(exc)},
                detector_name=self.name,
                execution_time_ms=round(elapsed_ms, 2),
            )

    @abstractmethod
    async def analyze(self, **kwargs: Any) -> DetectionResult:
        """Run the actual detection logic.  Subclasses *must* implement."""
        ...

    # ------------------------------------------------------------------
    # Optional lifecycle hooks
    # ------------------------------------------------------------------

    def load_model(self) -> None:
        """Override to load weights / resources at startup."""
        self._is_ready = True

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} ready={self._is_ready}>"
