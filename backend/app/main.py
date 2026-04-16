"""FastAPI application entry point."""

from contextlib import asynccontextmanager
import time
from typing import AsyncGenerator
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.exceptions import ObeliskException
from app.core.logging import setup_logger
from app.core.observability import (
    HTTP_REQUESTS_IN_PROGRESS,
    observe_http_request,
)
from app.core.request_context import reset_request_id, set_request_id

logger = setup_logger(__name__)
settings = get_settings()


def _resolve_cors_origins() -> list[str]:
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

    if settings.environment == "local" or settings.allow_localhost_cors_in_non_local:
        return origins

    blocked_prefixes = (
        "http://localhost",
        "http://127.0.0.1",
        "https://localhost",
        "https://127.0.0.1",
    )
    filtered = [
        origin for origin in origins
        if not origin.startswith(blocked_prefixes)
    ]

    if not filtered:
        raise RuntimeError(
            "Non-local runtime requires at least one non-local CORS origin.",
        )

    return filtered


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting OBELISK backend …")
    logger.info("Debug mode: %s", settings.debug)

    from app.db.session import engine
    from app.db.base import Base
    from app.core.readiness import run_startup_readiness_or_raise

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created")

    if settings.enable_startup_readiness_checks:
        app.state.startup_readiness = run_startup_readiness_or_raise(
            strict=settings.strict_startup_checks,
            include_dependencies=settings.startup_check_dependencies,
        )
    else:
        app.state.startup_readiness = {
            "status": "skipped",
            "ready": True,
            "checks": {},
            "failures": [],
        }

    yield

    logger.info("Shutting down OBELISK backend …")


app = FastAPI(
    title="OBELISK",
    description=(
        "Omniscient Behavioral Entity Leveraging Intelligent "
        "Surveillance for Kill-chain prevention — "
        "AI‑powered supply‑chain attack detection."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_resolve_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)


@app.middleware("http")
async def add_request_observability(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid4())
    token = set_request_id(request_id)

    method = request.method.upper()
    path = request.url.path
    in_flight = HTTP_REQUESTS_IN_PROGRESS.labels(method, path)
    in_flight.inc()

    started = time.perf_counter()
    response = None
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        duration_seconds = max(time.perf_counter() - started, 0.0)
        observe_http_request(method, path, status_code, duration_seconds)
        in_flight.dec()
        logger.info(
            "request_complete method=%s path=%s status=%s duration_ms=%.2f",
            method,
            path,
            status_code,
            duration_seconds * 1000,
        )
        reset_request_id(token)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


@app.exception_handler(ObeliskException)
async def obelisk_exception_handler(request: Request, exc: ObeliskException):

    logger.error("ObeliskException: %s", exc)
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):

    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


from app.api.routes.health import router as health_router      # noqa: E402
from app.api.routes.auth import router as auth_router          # noqa: E402
from app.api.routes.packages import router as packages_router  # noqa: E402
from app.api.routes.stats import router as stats_router        # noqa: E402
from app.api.routes.alerts import router as alerts_router      # noqa: E402
from app.api.routes.crawler import router as crawler_router    # noqa: E402
from app.api.routes.websocket import router as ws_router       # noqa: E402

app.include_router(health_router, tags=["health"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(packages_router, prefix="/api/packages", tags=["packages"])
app.include_router(stats_router, prefix="/api/stats", tags=["stats"])
app.include_router(alerts_router, prefix="/api/alerts", tags=["alerts"])
app.include_router(crawler_router, prefix="/api/crawler", tags=["crawler"])
app.include_router(ws_router, tags=["websocket"])


@app.get("/")
async def root():
    return {
        "name": "OBELISK",
        "version": "0.1.0",
        "status": "operational",
    }
