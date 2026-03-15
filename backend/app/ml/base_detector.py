"""Abstract base class for all ML detectors."""

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
    weight: float = 0.0

    def __init__(self) -> None:
        self._is_ready = False
        logger.debug("Initialising detector: %s v%s", self.name, self.version)

    async def run(self, **kwargs: Any) -> DetectionResult:
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
            # return zero-score rather than crashing the pipeline
            return DetectionResult(
                score=0.0,
                confidence=0.0,
                evidence={"error": str(exc)},
                detector_name=self.name,
                execution_time_ms=round(elapsed_ms, 2),
            )

    @abstractmethod
    async def analyze(self, **kwargs: Any) -> DetectionResult:
        ...

    def load_model(self) -> None:
        self._is_ready = True

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} ready={self._is_ready}>"
