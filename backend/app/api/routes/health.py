"""Health check endpoint."""

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from app.core.observability import collect_worker_observability, render_metrics
from app.core.readiness import collect_runtime_readiness

router = APIRouter()


@router.get("/health")
async def health_check(request: Request):
    startup_status = getattr(request.app.state, "startup_readiness", {}).get("status", "unknown")
    return {
        "status": "healthy",
        "service": "obelisk-backend",
        "startup_readiness": startup_status,
    }


@router.get("/health/ready")
async def readiness_check(request: Request):
    startup = getattr(request.app.state, "startup_readiness", {
        "status": "unknown",
        "ready": False,
        "checks": {},
        "failures": ["startup readiness state unavailable"],
    })
    runtime = collect_runtime_readiness(include_dependencies=True)

    ready = bool(startup.get("ready", False)) and runtime["ready"]
    payload = {
        "status": "ready" if ready else "degraded",
        "service": "obelisk-backend",
        "startup": startup,
        "runtime": runtime,
    }
    return JSONResponse(status_code=200 if ready else 503, content=payload)


@router.get("/health/worker")
async def worker_health_check():
    worker_obs = collect_worker_observability()
    healthy = bool(worker_obs.get("worker", {}).get("healthy", False))

    payload = {
        "status": "healthy" if healthy else "degraded",
        "service": "obelisk-worker",
        "worker": worker_obs.get("worker", {}),
        "queue": worker_obs.get("queue", {}),
    }
    return JSONResponse(status_code=200 if healthy else 503, content=payload)


@router.get("/metrics")
async def metrics_endpoint():
    payload, content_type = render_metrics()
    return Response(content=payload, media_type=content_type)
