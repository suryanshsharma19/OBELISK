"""Analysis service - orchestrates the full detection pipeline."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import AnalysisError
from app.core.logging import setup_logger
from app.db import models as orm
from app.models.analysis import AnalysisResult, DetectionResult
from app.ml.anomaly_detector import AnomalyDetector
from app.ml.behavior_analyzer import BehaviorAnalyzer
from app.ml.code_analyzer import CodeAnalyzer
from app.ml.gnn_analyzer import GNNAnalyzer
from app.ml.risk_scorer import RiskScorer
from app.ml.typosquat import TyposquattingDetector

logger = setup_logger(__name__)

# detector singletons
_typosquat = TyposquattingDetector()
_code_analyzer = CodeAnalyzer()
_behavior = BehaviorAnalyzer()
_anomaly = AnomalyDetector()
_gnn = GNNAnalyzer()
_risk_scorer = RiskScorer()


async def analyze_package(
    name: str,
    version: str,
    registry: str,
    code: Optional[str],
    db: Session,
) -> dict[str, Any]:
    logger.info("Starting analysis for %s@%s (%s)", name, version, registry)

    # check cache
    cache_key = f"analysis:{registry}:{name}:{version}"
    cached = _get_cached_result(cache_key)
    if cached is not None:
        logger.info("Cache hit for %s", cache_key)
        return cached

    # fetch registry metadata
    metadata = await _fetch_metadata(name, version, registry)

    # If no code was provided, try to get it from the registry response
    if not code:
        code = metadata.get("code", "")

    # Extract maintainer info (best-effort)
    maintainer_data = _extract_maintainer(metadata)

    # Extract dependency list
    dependencies = _extract_dependencies(metadata)

    # run all detectors in parallel
    try:
        typo_res, code_res, behav_res, anomaly_res, gnn_res = await asyncio.gather(
            _typosquat.run(package_name=name),
            _code_analyzer.run(code=code or ""),
            _behavior.run(
                package_name=name,
                registry=registry,
                metadata=metadata,
                code=code or "",
            ),
            _anomaly.run(maintainer_data=maintainer_data),
            _gnn.run(package_name=name, dependencies=dependencies),
        )
    except Exception as exc:
        logger.error("Detector pipeline failed: %s", exc)
        raise AnalysisError(
            "One or more detectors failed",
            details={"error": str(exc)},
        ) from exc

    # calculate combined risk score
    detection_results = {
        "typosquatting": typo_res,
        "code_analysis": code_res,
        "behavior": behav_res,
        "maintainer": anomaly_res,
        "dependency": gnn_res,
    }
    analysis: AnalysisResult = _risk_scorer.calculate_risk(detection_results)

    # persist to PostgreSQL
    package_row, analysis_row = _persist_to_db(
        db, name, version, registry, metadata, analysis, detection_results,
    )

    # persist to Neo4j (best-effort)
    _persist_to_neo4j(name, version, registry, analysis.risk_score, analysis.is_malicious, dependencies)

    # cache in Redis
    response = _build_response(package_row, analysis, detection_results)
    _cache_result(cache_key, response)

    # alert if critical
    if analysis.threat_level in ("high", "critical"):
        _create_alert(db, package_row, analysis)

    logger.info(
        "Analysis complete: %s@%s → score=%.2f level=%s",
        name, version, analysis.risk_score, analysis.threat_level,
    )
    return response


async def _fetch_metadata(name: str, version: str, registry: str) -> dict[str, Any]:
    try:
        from app.services.registry_monitor import fetch_package_metadata
        return await fetch_package_metadata(name, version, registry)
    except Exception as exc:
        logger.warning("Could not fetch registry metadata for %s: %s", name, exc)
        return {}


def _extract_maintainer(metadata: dict[str, Any]) -> dict[str, Any]:
    maintainer = metadata.get("maintainer", {})
    if not maintainer:
        # npm-style "author" field
        author = metadata.get("author", {})
        if isinstance(author, str):
            return {"email": "", "account_age_days": 365, "total_packages": 1}
        maintainer = author

    return {
        "email": maintainer.get("email", ""),
        "account_age_days": maintainer.get("account_age_days", 365),
        "total_packages": maintainer.get("total_packages", 1),
        "has_verified_email": maintainer.get("has_verified_email", True),
        "github_repos": maintainer.get("github_repos", 1),
        "previous_downloads": maintainer.get("previous_downloads", 1),
    }


def _extract_dependencies(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    deps = metadata.get("dependencies", {})
    if isinstance(deps, dict):
        return [
            {"name": dep_name, "version": dep_ver, "is_malicious": False, "risk_score": 0}
            for dep_name, dep_ver in deps.items()
        ]
    return deps if isinstance(deps, list) else []


def _persist_to_db(
    db: Session,
    name: str,
    version: str,
    registry: str,
    metadata: dict[str, Any],
    analysis: AnalysisResult,
    detection_results: dict[str, DetectionResult],
) -> tuple:
    try:
        # upsert package
        pkg = (
            db.query(orm.Package)
            .filter_by(name=name, version=version)
            .first()
        )
        if pkg is None:
            pkg = orm.Package(
                name=name,
                version=version,
                registry=registry,
                description=metadata.get("description", ""),
                author=metadata.get("author", {}).get("name", "") if isinstance(metadata.get("author"), dict) else str(metadata.get("author", "")),
                license=metadata.get("license", ""),
                repository_url=metadata.get("repository", {}).get("url", "") if isinstance(metadata.get("repository"), dict) else "",
            )
            db.add(pkg)

        pkg.risk_score = analysis.risk_score
        pkg.threat_level = analysis.threat_level
        pkg.is_malicious = analysis.is_malicious
        pkg.analyzed_at = datetime.now(timezone.utc)
        db.flush()

        # Create analysis record
        analysis_row = orm.Analysis(
            package_id=pkg.id,
            typosquatting_score=detection_results["typosquatting"].score,
            code_analysis_score=detection_results["code_analysis"].score,
            behavior_score=detection_results["behavior"].score,
            maintainer_score=detection_results["maintainer"].score,
            dependency_score=detection_results["dependency"].score,
            typosquatting_evidence=detection_results["typosquatting"].evidence,
            code_patterns=detection_results["code_analysis"].evidence,
            behaviors=detection_results["behavior"].evidence,
            maintainer_flags=detection_results["maintainer"].evidence,
            dependencies=detection_results["dependency"].evidence,
            confidence=analysis.confidence,
        )
        db.add(analysis_row)
        db.commit()
        db.refresh(pkg)

        return pkg, analysis_row

    except Exception as exc:
        db.rollback()
        logger.error("Failed to persist analysis to DB: %s", exc)
        raise AnalysisError("Database persistence failed", details={"error": str(exc)}) from exc


def _persist_to_neo4j(
    name: str,
    version: str,
    registry: str,
    risk_score: float,
    is_malicious: bool,
    dependencies: list[dict[str, Any]],
) -> None:
    try:
        from app.db.neo4j_client import neo4j_client

        neo4j_client.create_package_node(name, version, registry, risk_score, is_malicious)
        for dep in dependencies:
            dep_version = dep.get("version", "0.0.0")
            if isinstance(dep_version, str) and dep_version.startswith("^"):
                dep_version = dep_version[1:]
            neo4j_client.create_dependency_edge(
                name, version, dep["name"], dep_version,
            )
    except Exception as exc:
        logger.warning("Neo4j persistence skipped: %s", exc)


def _get_cached_result(key: str) -> Optional[dict[str, Any]]:
    try:
        from app.db.redis_client import redis_client
        return redis_client.get_json(key)
    except Exception:
        return None


def _cache_result(key: str, data: dict[str, Any]) -> None:
    try:
        from app.db.redis_client import redis_client
        redis_client.set_json(key, data, ttl=3600)
    except Exception as exc:
        logger.warning("Redis cache write failed: %s", exc)


def _create_alert(db: Session, package: orm.Package, analysis: AnalysisResult) -> None:
    try:
        alert = orm.Alert(
            package_id=package.id,
            title=f"Threat detected: {package.name}@{package.version}",
            description=(
                f"Risk score {analysis.risk_score:.1f} ({analysis.threat_level}). "
                f"Confidence: {analysis.confidence:.0%}."
            ),
            threat_level=analysis.threat_level,
        )
        db.add(alert)
        db.commit()
        logger.info("Alert created for %s (level=%s)", package.name, analysis.threat_level)
    except Exception as exc:
        db.rollback()
        logger.warning("Failed to create alert: %s", exc)


def _build_response(
    package: orm.Package,
    analysis: AnalysisResult,
    detection_results: dict[str, DetectionResult],
) -> dict[str, Any]:
    return {
        "package": {
            "id": package.id,
            "name": package.name,
            "version": package.version,
            "registry": package.registry.value if hasattr(package.registry, "value") else str(package.registry),
            "risk_score": analysis.risk_score,
            "threat_level": analysis.threat_level,
            "is_malicious": analysis.is_malicious,
            "analyzed_at": package.analyzed_at.isoformat() if package.analyzed_at else None,
        },
        "analysis": {
            "risk_score": analysis.risk_score,
            "threat_level": analysis.threat_level,
            "is_malicious": analysis.is_malicious,
            "confidence": analysis.confidence,
            "breakdown": analysis.detection_details.get("breakdown", {}),
        },
        "detection_details": {
            name: {
                "score": result.score,
                "confidence": result.confidence,
                "evidence": result.evidence,
                "execution_time_ms": result.execution_time_ms,
            }
            for name, result in detection_results.items()
        },
    }
