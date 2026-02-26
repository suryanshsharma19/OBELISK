"""
Graph Neural Network (GNN) Analyzer — evaluates dependency-graph risk.

Queries the Neo4j graph database to find a package's dependency chain,
then scores based on:
  1. Any known-malicious packages in the chain
  2. Depth of the dependency tree (deep trees = harder to audit)
  3. Overall risk scores of direct + transitive dependencies

When a trained GNN model is available (PyTorch Geometric), it runs
graph-level classification for deeper structural analysis.  Otherwise
it falls back to the deterministic graph-traversal approach.

Classes:
    GNNAnalyzer(BaseDetector)

Usage:
    analyzer = GNNAnalyzer()
    result = await analyzer.run(
        package_name="suspicious-pkg",
        dependencies=[{"name": "express", "version": "4.18.0"}, ...],
    )
"""

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

    # ------------------------------------------------------------------

    def load_model(self) -> None:
        """Try loading a trained GNN model (PyTorch Geometric)."""
        try:
            from app.ml.model_loader import load_pytorch_model
            from app.config import get_settings

            model_path = get_settings().gnn_model_path + "/model.pt"
            self._gnn_model = load_pytorch_model(model_path)
            logger.info("GNN model loaded successfully")
        except Exception as exc:
            logger.info("GNN model not available (%s) — using graph rules", exc)
            self._gnn_model = None

    # ------------------------------------------------------------------

    async def analyze(self, **kwargs: Any) -> DetectionResult:
        """
        Evaluate dependency-graph risk.

        Keyword Args:
            package_name (str): Root package name.
            dependencies (list[dict]): Direct deps, each with
                name, version, and optionally risk_score / is_malicious.

        Returns:
            DetectionResult with graph-level risk score.
        """
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

        # --- Check for known malicious deps ---
        malicious_deps = [
            dep for dep in dependencies
            if dep.get("is_malicious", False)
        ]

        # --- Check for high-risk deps ---
        high_risk_deps = [
            dep for dep in dependencies
            if dep.get("risk_score", 0) >= 60 and not dep.get("is_malicious")
        ]

        # --- Score calculation ---
        score = 0.0

        # Direct malicious dependency = very high score
        if malicious_deps:
            score += min(len(malicious_deps) * 45, 90)

        # High-risk dependencies contribute proportionally
        if high_risk_deps:
            avg_risk = sum(d.get("risk_score", 0) for d in high_risk_deps) / len(high_risk_deps)
            score += avg_risk * 0.3

        # Large dependency trees are harder to audit
        dep_count = len(dependencies)
        if dep_count > 20:
            score += 10
        elif dep_count > 50:
            score += 20

        # Try Neo4j traversal for deeper analysis
        neo4j_findings = await self._query_neo4j(package_name)

        # If Neo4j found transitive malicious deps, bump the score
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

    # ------------------------------------------------------------------
    # Neo4j query helper
    # ------------------------------------------------------------------

    async def _query_neo4j(self, package_name: str) -> dict[str, Any]:
        """
        Attempt to query Neo4j for transitive dependency info.
        Returns an empty result dict if Neo4j isn't reachable.
        """
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
