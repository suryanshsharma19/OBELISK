"""GNN analyzer - evaluates dependency-graph risk via Neo4j + optional GNN model."""

from __future__ import annotations

from typing import Any

from app.core.logging import setup_logger
from app.ml.base_detector import BaseDetector
from app.models.analysis import DetectionResult

logger = setup_logger(__name__)


class GNNAnalyzer(BaseDetector):
    """Score dependency-graph risk using Neo4j traversal + optional GNN."""

    name = "dependency"
    version = "1.0.0"
    weight = 0.10

    def __init__(self) -> None:
        super().__init__()
        self._gnn_model = None
        self._is_ready = True

    def load_model(self) -> None:
        try:
            from app.ml.model_loader import load_pytorch_model
            from app.config import get_settings

            model_path = get_settings().gnn_model_path + "/model.pt"
            self._gnn_model = load_pytorch_model(model_path)
            logger.info("GNN model loaded successfully")
        except Exception as exc:
            logger.info("GNN model not available (%s) — using graph rules", exc)
            self._gnn_model = None

    async def analyze(self, **kwargs: Any) -> DetectionResult:
        package_name: str = kwargs.get("package_name", "")
        dependencies: list[dict[str, Any]] = kwargs.get("dependencies", [])

        if not dependencies:
            return DetectionResult(
                score=0.0,
                confidence=0.8,
                evidence={
                    "total_dependencies": 0,
                    "note": "No dependencies to analyse",
                },
            )

        # check for known malicious deps
        malicious_deps = [
            dep for dep in dependencies
            if dep.get("is_malicious", False)
        ]

        # check for high-risk deps
        high_risk_deps = [
            dep for dep in dependencies
            if dep.get("risk_score", 0) >= 60 and not dep.get("is_malicious")
        ]

        # score calculation
        score = 0.0

        # direct malicious dependency
        if malicious_deps:
            score += min(len(malicious_deps) * 45, 90)

        # high-risk deps contribute proportionally
        if high_risk_deps:
            avg_risk = sum(d.get("risk_score", 0) for d in high_risk_deps) / len(high_risk_deps)
            score += avg_risk * 0.3

        # large dep trees are harder to audit
        dep_count = len(dependencies)
        if dep_count > 50:
            score += 20
        elif dep_count > 20:
            score += 10

        # try Neo4j for deeper analysis
        neo4j_findings = await self._query_neo4j(package_name)

        # bump score if transitive malicious deps found
        if neo4j_findings.get("transitive_malicious", 0) > 0:
            score += 15

        score = min(score, 100.0)
        confidence = 0.7 if not self._gnn_model else 0.9

        return DetectionResult(
            score=round(score, 2),
            confidence=confidence,
            evidence={
                "has_malicious_dependencies": len(malicious_deps) > 0,
                "malicious_deps": [
                    {"name": d.get("name"), "risk_score": d.get("risk_score", 0)}
                    for d in malicious_deps
                ],
                "high_risk_deps": [
                    {"name": d.get("name"), "risk_score": d.get("risk_score", 0)}
                    for d in high_risk_deps
                ],
                "total_dependencies": dep_count,
                "dependency_depth": neo4j_findings.get("max_depth", 1),
                "gnn_model_used": self._gnn_model is not None,
                "neo4j_available": neo4j_findings.get("available", False),
            },
        )

    async def _query_neo4j(self, package_name: str) -> dict[str, Any]:
        try:
            from app.db.neo4j_client import neo4j_client

            mal_chain = neo4j_client.find_malicious_in_chain(package_name)
            all_deps = neo4j_client.get_dependencies(package_name, max_depth=5)

            max_depth = max((d.get("depth", 1) for d in all_deps), default=1)

            return {
                "available": True,
                "transitive_malicious": len(mal_chain),
                "total_transitive": len(all_deps),
                "max_depth": max_depth,
            }
        except Exception as exc:
            logger.debug("Neo4j query skipped: %s", exc)
            return {
                "available": False,
                "transitive_malicious": 0,
                "total_transitive": 0,
                "max_depth": 1,
            }
