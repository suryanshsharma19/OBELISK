"""
OBELISK — FastAPI application entry point.

Sets up the FastAPI app with all middleware, exception handlers,
and route registrations. This is the module that uvicorn boots.

Usage:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.exceptions import ObeliskException
from app.core.logging import setup_logger

logger = setup_logger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Lifespan — runs once on startup and once on shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle startup / shutdown tasks for the application."""
    logger.info("Starting OBELISK backend …")
    logger.info("Debug mode: %s", settings.debug)

    # Import here to avoid circular imports with models
    from app.db.session import engine
    from app.db.base import Base

    # Create all tables if they don't exist yet (dev convenience)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created")

    yield  # ← app is running

    logger.info("Shutting down OBELISK backend …")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

# Allow the React dev server and any local tools to hit the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(ObeliskException)
async def obelisk_exception_handler(request: Request, exc: ObeliskException):
    """Catch any of our custom exceptions and return a tidy JSON error."""
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
    """Last-resort handler so the client never sees a raw traceback."""
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------

from app.api.routes.health import router as health_router      # noqa: E402
from app.api.routes.packages import router as packages_router  # noqa: E402
from app.api.routes.stats import router as stats_router        # noqa: E402
from app.api.routes.alerts import router as alerts_router      # noqa: E402
from app.api.routes.crawler import router as crawler_router    # noqa: E402

app.include_router(health_router, tags=["health"])
app.include_router(packages_router, prefix="/api/packages", tags=["packages"])
app.include_router(stats_router, prefix="/api/stats", tags=["stats"])
app.include_router(alerts_router, prefix="/api/alerts", tags=["alerts"])
app.include_router(crawler_router, prefix="/api/crawler", tags=["crawler"])


# Root endpoint — quick sanity check
@app.get("/")
async def root():
    return {
        "name": "OBELISK",
        "version": "0.1.0",
        "status": "operational",
    }
