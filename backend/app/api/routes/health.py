"""
Health check endpoint.

Provides a quick /health route that Docker health checks and
load balancers can hit to verify the service is up.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Return basic health status for monitoring tools."""
    return {"status": "healthy", "service": "obelisk-backend"}
