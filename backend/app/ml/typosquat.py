"""Typosquatting detector - catches packages mimicking popular names."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from Levenshtein import distance as levenshtein_distance
from Levenshtein import ratio as levenshtein_ratio

from app.core.logging import setup_logger
from app.ml.base_detector import BaseDetector
from app.models.analysis import DetectionResult
from app.utils.constants import POPULAR_PACKAGES

logger = setup_logger(__name__)

MAX_EDIT_DISTANCE = 2
MIN_SIMILARITY_RATIO = 0.85
MAX_POPULAR_PACKAGE_CORPUS = 10_000


class TyposquattingDetector(BaseDetector):
    """Detect package names that are suspiciously close to well-known ones."""

    name = "typosquatting"
    version = "1.0.0"
    weight = 0.25

    def __init__(self) -> None:
        super().__init__()
        self._popular = self._load_popular_packages()
        self._is_ready = True

    def _load_popular_packages(self) -> list[str]:
        candidates = {pkg.lower().strip() for pkg in POPULAR_PACKAGES if pkg.strip()}

        dataset_candidates = [
            Path(__file__).resolve().parents[2] / "ml_models" / "datasets" / "popular_packages.json",
            Path(__file__).resolve().parents[2] / "ml_models" / "datasets" / "popular_packages.txt",
        ]

        for dataset_path in dataset_candidates:
            if not dataset_path.exists():
                continue
            try:
                if dataset_path.suffix == ".json":
                    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
                    if isinstance(payload, list):
                        for item in payload:
                            if isinstance(item, str) and item.strip():
                                candidates.add(item.lower().strip())
                else:
                    for line in dataset_path.read_text(encoding="utf-8").splitlines():
                        name = line.strip().lower()
                        if name:
                            candidates.add(name)
            except Exception as exc:
                logger.warning("Failed to load popular package corpus from %s: %s", dataset_path, exc)

        # Keep the most practical corpus size for startup/runtime latency.
        corpus = sorted(candidates)
        if len(corpus) > MAX_POPULAR_PACKAGE_CORPUS:
            corpus = corpus[:MAX_POPULAR_PACKAGE_CORPUS]

        logger.info("Typosquatting corpus loaded: %d package names", len(corpus))
        return corpus

    async def analyze(self, **kwargs: Any) -> DetectionResult:
        package_name: str = kwargs.get("package_name", "")
        if not package_name:
            return DetectionResult(score=0.0, confidence=0.0)

        target = package_name.lower().strip()
        similar_packages: list[dict[str, Any]] = []
        best_ratio = 0.0

        for popular in self._popular:
            if target == popular:
                return DetectionResult(
                    score=0.0,
                    confidence=1.0,
                    evidence={"exact_match": popular},
                )

            dist = levenshtein_distance(target, popular)
            sim_ratio = levenshtein_ratio(target, popular)

            if dist <= MAX_EDIT_DISTANCE or sim_ratio >= MIN_SIMILARITY_RATIO:
                similar_packages.append({
                    "name": popular,
                    "similarity": round(sim_ratio, 4),
                    "distance": dist,
                })
                best_ratio = max(best_ratio, sim_ratio)

        similar_packages.sort(key=lambda x: x["similarity"], reverse=True)

        if not similar_packages:
            score = 0.0
            is_typosquat = False
        else:
            score = round(best_ratio * 100, 2)
            is_typosquat = True

        confidence = min(best_ratio * 1.1, 1.0) if similar_packages else 0.0

        return DetectionResult(
            score=score,
            confidence=round(confidence, 3),
            evidence={
                "is_typosquatting": is_typosquat,
                "similar_packages": similar_packages[:5],  # top 5
                "method": "levenshtein",
                "threshold_distance": MAX_EDIT_DISTANCE,
                "threshold_ratio": MIN_SIMILARITY_RATIO,
                "best_ratio": round(best_ratio, 4),
                "corpus_size": len(self._popular),
            },
        )
