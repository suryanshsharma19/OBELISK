"""Package routes - analyse, list, and retrieve package details."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
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
from app.utils.formatters import format_alert_summary

logger = setup_logger(__name__)

router = APIRouter()


@router.post("/analyze", response_model=None)
async def analyze_package(request: AnalyzeRequest, db: Session = Depends(get_db)):
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
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/list", response_model=None)
async def list_packages(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    threat_level: Optional[str] = Query(None),
    registry: Optional[str] = Query(None),
    sort: str = Query("analyzed_at_desc"),
    db: Session = Depends(get_db),
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
            }
            for pkg in packages
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + limit < total,
    }


@router.get("/{package_id}", response_model=None)
async def get_package_detail(package_id: int, db: Session = Depends(get_db)):
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
    if analysis:
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
            "risk_score": round(package.risk_score or 0.0, 2),
            "threat_level": package.threat_level.value if hasattr(package.threat_level, "value") else str(package.threat_level or "safe"),
            "is_malicious": package.is_malicious or False,
            "analyzed_at": package.analyzed_at.isoformat() if package.analyzed_at else None,
        },
        "analysis": analysis_data,
        "alerts": [format_alert_summary(a) for a in alerts],
    }
