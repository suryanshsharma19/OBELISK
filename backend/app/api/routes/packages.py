"""Package routes - analyse, list, and retrieve package details."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import enforce_rate_limit, get_current_user, get_db
from app.core.logging import setup_logger
from app.db.models import Alert, Analysis, Package
from app.schemas.package import (
    AnalyzeRequest,
    AnalyzeResponse,
    PackageDetailResponse,
    PackageListResponse,
)
from app.models.package import PackageResponse
from app.services import analysis_service
from app.utils.constants import DETECTION_WEIGHTS
from app.utils.formatters import format_alert_summary

logger = setup_logger(__name__)

router = APIRouter()


def _extract_dependency_items(raw_dependencies: object) -> list[dict[str, object]]:
    if not isinstance(raw_dependencies, dict):
        return []

    if isinstance(raw_dependencies.get("dependencies"), list):
        items = raw_dependencies.get("dependencies", [])
    else:
        items = []
        for bucket in ("malicious_deps", "high_risk_deps"):
            bucket_items = raw_dependencies.get(bucket, [])
            if isinstance(bucket_items, list):
                items.extend(bucket_items)

    cleaned: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        cleaned.append(
            {
                "name": name,
                "version": str(item.get("version", "") or ""),
                "risk_score": float(item.get("risk_score", 0) or 0),
                "is_malicious": bool(item.get("is_malicious", False)),
            }
        )

    return cleaned


def _build_breakdown(analysis: Analysis) -> dict[str, dict[str, float]]:
    score_map = {
        "typosquatting": float(analysis.typosquatting_score or 0),
        "code_analysis": float(analysis.code_analysis_score or 0),
        "behavior": float(analysis.behavior_score or 0),
        "maintainer": float(analysis.maintainer_score or 0),
        "dependency": float(analysis.dependency_score or 0),
    }
    breakdown: dict[str, dict[str, float]] = {}

    for detector_name, score in score_map.items():
        weight = float(DETECTION_WEIGHTS.get(detector_name, 0))
        breakdown[detector_name] = {
            "score": round(score, 2),
            "weight": weight,
            "contribution": round(score * weight, 2),
        }

    return breakdown


@router.post("/analyze", response_model=None)
async def analyze_package(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
    __: None = Depends(enforce_rate_limit),
):
    logger.info("Analyze request: %s@%s (%s)", request.name, request.version, request.registry)

    try:
        result = await analysis_service.analyze_package(
            name=request.name,
            version=request.version,
            registry=request.registry,
            code=request.code,
            db=db,
        )
        return result
    except Exception as exc:
        logger.error("Analysis failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Analysis failed due to an internal error",
        ) from exc


@router.get("/list", response_model=None)
async def list_packages(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    threat_level: Optional[str] = Query(None),
    registry: Optional[str] = Query(None),
    sort: str = Query("risk_score_desc"),
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    query = db.query(Package)

    # Apply filters
    if threat_level:
        query = query.filter(Package.threat_level == threat_level)
    if registry:
        query = query.filter(Package.registry == registry)

    # Sorting
    if sort == "risk_score_desc":
        query = query.order_by(Package.risk_score.desc())
    elif sort == "risk_score_asc":
        query = query.order_by(Package.risk_score.asc())
    elif sort == "analyzed_at_asc":
        query = query.order_by(Package.analyzed_at.asc())
    else:
        # Default: newest first
        query = query.order_by(Package.analyzed_at.desc())

    total = query.count()
    packages = query.offset(skip).limit(limit).all()

    return {
        "packages": [
            {
                "id": pkg.id,
                "name": pkg.name,
                "version": pkg.version,
                "registry": pkg.registry.value if hasattr(pkg.registry, "value") else str(pkg.registry),
                "risk_score": round(pkg.risk_score or 0.0, 2),
                "threat_level": pkg.threat_level.value if hasattr(pkg.threat_level, "value") else str(pkg.threat_level or "safe"),
                "is_malicious": pkg.is_malicious or False,
                "analyzed_at": pkg.analyzed_at.isoformat() if pkg.analyzed_at else None,
                "description": pkg.description or "",
                "author": pkg.author or "",
                "weekly_downloads": int(pkg.weekly_downloads or 0),
            }
            for pkg in packages
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + limit < total,
    }


@router.get("/{package_id}", response_model=None)
async def get_package_detail(
    package_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    package = db.query(Package).filter(Package.id == package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    # Get the latest analysis
    analysis = (
        db.query(Analysis)
        .filter(Analysis.package_id == package_id)
        .order_by(Analysis.created_at.desc())
        .first()
    )

    # Get associated alerts
    alerts = (
        db.query(Alert)
        .filter(Alert.package_id == package_id)
        .order_by(Alert.created_at.desc())
        .limit(10)
        .all()
    )

    analysis_data = None
    dependencies: list[dict[str, object]] = []
    if analysis:
        dependencies = _extract_dependency_items(analysis.dependencies)

        if not dependencies:
            try:
                from app.services.graph_service import get_package_graph

                graph = get_package_graph(package.name, max_depth=3)
                graph_deps = graph.get("dependencies", []) if isinstance(graph, dict) else []
                for dep in graph_deps:
                    if not isinstance(dep, dict):
                        continue
                    dep_name = str(dep.get("name", "")).strip()
                    if not dep_name:
                        continue
                    dependencies.append(
                        {
                            "name": dep_name,
                            "version": str(dep.get("version", "") or ""),
                            "risk_score": float(dep.get("risk_score", 0) or 0),
                            "is_malicious": bool(dep.get("is_malicious", False)),
                        }
                    )
            except Exception:
                # Keep detail endpoint resilient even when graph backend is unavailable.
                pass

        analysis_data = {
            "typosquatting_score": analysis.typosquatting_score,
            "code_analysis_score": analysis.code_analysis_score,
            "behavior_score": analysis.behavior_score,
            "maintainer_score": analysis.maintainer_score,
            "dependency_score": analysis.dependency_score,
            "typosquatting_evidence": analysis.typosquatting_evidence,
            "code_patterns": analysis.code_patterns,
            "behaviors": analysis.behaviors,
            "maintainer_flags": analysis.maintainer_flags,
            "dependencies": analysis.dependencies,
            "confidence": analysis.confidence,
            "breakdown": _build_breakdown(analysis),
        }

    return {
        "package": {
            "id": package.id,
            "name": package.name,
            "version": package.version,
            "registry": package.registry.value if hasattr(package.registry, "value") else str(package.registry),
            "description": package.description,
            "author": package.author,
            "license": package.license,
            "repository_url": package.repository_url,
            "homepage_url": package.homepage_url,
            "risk_score": round(package.risk_score or 0.0, 2),
            "threat_level": package.threat_level.value if hasattr(package.threat_level, "value") else str(package.threat_level or "safe"),
            "is_malicious": package.is_malicious or False,
            "weekly_downloads": int(package.weekly_downloads or 0),
            "analyzed_at": package.analyzed_at.isoformat() if package.analyzed_at else None,
            "published_at": package.published_at.isoformat() if package.published_at else None,
        },
        "analysis": analysis_data,
        "alerts": [format_alert_summary(a) for a in alerts],
        "dependencies": dependencies,
    }
