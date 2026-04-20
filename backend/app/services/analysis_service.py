"""Analysis service - orchestrates the full detection pipeline."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Awaitable, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import AnalysisError
from app.core.logging import setup_logger
from app.core.observability import (
    mark_analysis_cache_error,
    mark_analysis_cache_hit,
    mark_analysis_cache_miss,
    observe_detector,
)
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


def load_detection_models() -> dict[str, bool]:
    """Load optional detector models once at startup."""
    statuses: dict[str, bool] = {}

    loaders = {
        "code_analysis": _code_analyzer,
        "maintainer": _anomaly,
        "dependency": _gnn,
    }

    for name, detector in loaders.items():
        try:
            detector.load_model()
            statuses[name] = True
            logger.info("Model loader executed for detector=%s", name)
        except Exception as exc:
            statuses[name] = False
            logger.warning("Model loader failed for detector=%s: %s", name, exc)

    return statuses


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
    cached, cache_outcome = _get_cached_result(cache_key)
    if cache_outcome == "hit":
        mark_analysis_cache_hit()
    elif cache_outcome == "miss":
        mark_analysis_cache_miss()
    else:
        mark_analysis_cache_error()

    if cached is not None:
        logger.info("Cache hit for %s", cache_key)
        await _emit_analysis_events(cached, from_cache=True)
        return cached

    # fetch registry metadata
    metadata = await _fetch_metadata(name, version, registry)

    # If no code was provided, try to get it from the registry response
    if not code:
        code = metadata.get("code", "")

    if not code:
        code = await _fetch_package_code(name, version, registry, metadata)

    # Extract maintainer info (best-effort)
    maintainer_data = _extract_maintainer(metadata)

    # Extract dependency list
    dependencies = _extract_dependencies(metadata)

    # run all detectors in parallel
    try:
        typo_res, code_res, behav_res, anomaly_res, gnn_res = await asyncio.gather(
            _run_detector("typosquatting", _typosquat.run(package_name=name)),
            _run_detector("code_analysis", _code_analyzer.run(code=code or "")),
            _run_detector(
                "behavior",
                _behavior.run(
                package_name=name,
                version=version,
                registry=registry,
                metadata=metadata,
                code=code or "",
            ),
            ),
            _run_detector("maintainer", _anomaly.run(maintainer_data=maintainer_data)),
            _run_detector("dependency", _gnn.run(package_name=name, dependencies=dependencies)),
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
    response = _build_response(package_row, analysis, detection_results, code=code or "")
    _cache_result(cache_key, response)

    await _emit_analysis_events(response, from_cache=False)

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


async def _fetch_package_code(
    name: str,
    version: str,
    registry: str,
    metadata: dict[str, Any],
) -> str:
    try:
        from app.services.registry_monitor import fetch_package_source_code

        return await fetch_package_source_code(
            name=name,
            version=version,
            registry=registry,
            metadata=metadata,
        )
    except Exception as exc:
        logger.warning("Package source fetch failed for %s@%s: %s", name, version, exc)
        return ""


async def _run_detector(name: str, detector_coro: Awaitable[DetectionResult]) -> DetectionResult:
    started = time.perf_counter()
    try:
        result = await detector_coro
        observe_detector(name, time.perf_counter() - started, failed=False)
        return result
    except Exception:
        observe_detector(name, time.perf_counter() - started, failed=True)
        raise


def _extract_maintainer(metadata: dict[str, Any]) -> dict[str, Any]:
    maintainer = metadata.get("maintainer", {})
    maintainers = metadata.get("maintainers", [])

    if not maintainer and maintainers and isinstance(maintainers[0], dict):
        maintainer = maintainers[0]

    if not maintainer:
        # npm-style "author" field
        author = metadata.get("author", {})
        if isinstance(author, str):
            return {
                "email": "",
                "account_age_days": metadata.get("maintainer_account_age_days", 365),
                "total_packages": metadata.get("maintainer_total_packages", 1),
                "has_verified_email": metadata.get("maintainer_has_verified_email", False),
                "github_repos": metadata.get("maintainer_github_repos", 0),
                "previous_downloads": metadata.get("maintainer_previous_downloads", 0),
            }
        maintainer = author

    return {
        "email": maintainer.get("email", ""),
        "account_age_days": maintainer.get(
            "account_age_days",
            metadata.get("maintainer_account_age_days", 365),
        ),
        "total_packages": maintainer.get(
            "total_packages",
            metadata.get("maintainer_total_packages", 1),
        ),
        "has_verified_email": maintainer.get(
            "has_verified_email",
            metadata.get("maintainer_has_verified_email", False),
        ),
        "github_repos": maintainer.get(
            "github_repos",
            metadata.get("maintainer_github_repos", 0),
        ),
        "previous_downloads": maintainer.get(
            "previous_downloads",
            metadata.get("maintainer_previous_downloads", metadata.get("weekly_downloads", 0)),
        ),
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
            .filter_by(name=name, version=version, registry=registry)
            .first()
        )
        author_name = ""
        if isinstance(metadata.get("author"), dict):
            author_name = str(metadata.get("author", {}).get("name", ""))
        elif isinstance(metadata.get("author"), str):
            author_name = metadata.get("author", "")

        repository_url = ""
        repository = metadata.get("repository")
        if isinstance(repository, dict):
            repository_url = str(repository.get("url", ""))
        elif isinstance(repository, str):
            repository_url = repository

        homepage_url = str(metadata.get("homepage", "") or "")
        weekly_downloads = int(metadata.get("weekly_downloads", 0) or 0)
        published_at = _parse_timestamp(metadata.get("published_at"))

        if pkg is None:
            pkg = orm.Package(
                name=name,
                version=version,
                registry=registry,
                description=metadata.get("description", ""),
                author=author_name,
                license=metadata.get("license", ""),
                repository_url=repository_url,
                homepage_url=homepage_url,
                weekly_downloads=weekly_downloads,
                published_at=published_at,
            )
            db.add(pkg)

        pkg.description = metadata.get("description", pkg.description)
        pkg.author = author_name or pkg.author
        pkg.license = metadata.get("license", pkg.license)
        pkg.repository_url = repository_url or pkg.repository_url
        pkg.homepage_url = homepage_url or pkg.homepage_url
        pkg.weekly_downloads = weekly_downloads
        if published_at:
            pkg.published_at = published_at

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


def _get_cached_result(key: str) -> tuple[Optional[dict[str, Any]], str]:
    try:
        from app.db.redis_client import redis_client
        cached = redis_client.get_json(key)
        if cached is None:
            return None, "miss"
        return cached, "hit"
    except Exception:
        return None, "error"


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
    code: str,
) -> dict[str, Any]:
    dependency_graph = _build_dependency_graph(package, detection_results)

    return {
        # Flattened fields kept for backward compatibility with existing frontend state mapping.
        "name": package.name,
        "version": package.version,
        "registry": package.registry.value if hasattr(package.registry, "value") else str(package.registry),
        "risk_score": analysis.risk_score,
        "threat_level": analysis.threat_level,
        "is_malicious": analysis.is_malicious,
        "confidence": analysis.confidence,
        "code": code,
        "dependency_graph": dependency_graph,
        "package": {
            "id": package.id,
            "name": package.name,
            "version": package.version,
            "registry": package.registry.value if hasattr(package.registry, "value") else str(package.registry),
            "risk_score": analysis.risk_score,
            "threat_level": analysis.threat_level,
            "is_malicious": analysis.is_malicious,
            "weekly_downloads": int(package.weekly_downloads or 0),
            "analyzed_at": package.analyzed_at.isoformat() if package.analyzed_at else None,
        },
        "analysis": {
            "risk_score": analysis.risk_score,
            "threat_level": analysis.threat_level,
            "is_malicious": analysis.is_malicious,
            "confidence": analysis.confidence,
            "breakdown": analysis.detection_details.get("breakdown", {}),
            "calibration": analysis.detection_details.get("calibration", {}),
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


def _build_dependency_graph(
    package: orm.Package,
    detection_results: dict[str, DetectionResult],
) -> dict[str, Any]:
    dependency_result = detection_results.get("dependency")
    dependency_evidence = dependency_result.evidence if dependency_result else {}
    dependencies = dependency_evidence.get("dependencies", [])

    nodes = [
        {
            "id": package.name,
            "name": package.name,
            "riskScore": float(package.risk_score or 0),
            "isRoot": True,
        }
    ]
    edges = []
    seen_nodes = {package.name}

    if isinstance(dependencies, list):
        for dep in dependencies:
            if not isinstance(dep, dict):
                continue
            dep_name = str(dep.get("name", "")).strip()
            if not dep_name:
                continue

            if dep_name not in seen_nodes:
                nodes.append(
                    {
                        "id": dep_name,
                        "name": dep_name,
                        "riskScore": float(dep.get("risk_score", 0) or 0),
                        "isRoot": False,
                    }
                )
                seen_nodes.add(dep_name)
            edges.append(
                {
                    "source": package.name,
                    "target": dep_name,
                }
            )

    return {"nodes": nodes, "edges": edges}


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            return None
    return None


async def _emit_analysis_events(response: dict[str, Any], from_cache: bool) -> None:
    payload = {
        "package": response.get("package", {}),
        "analysis": response.get("analysis", {}),
        "from_cache": from_cache,
    }

    try:
        from app.api.routes.websocket import manager

        await manager.broadcast("analysis_complete", payload)

        threat_level = str(payload["analysis"].get("threat_level", "")).lower()
        if threat_level in {"high", "critical"}:
            await manager.broadcast("threat_detected", payload)
    except Exception as exc:
        logger.warning("WebSocket broadcast skipped: %s", exc)
