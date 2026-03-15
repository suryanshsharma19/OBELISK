"""Crawler control routes - start/stop/status for the registry monitor."""

import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.core.logging import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

# in-memory crawler state
_crawler_state: dict[str, Any] = {
    "running": False,
    "task": None,
    "last_check": None,
    "packages_checked": 0,
    "threats_found": 0,
}


@router.post("/start")
async def start_crawler(_: dict = Depends(get_current_user)):
    if _crawler_state["running"]:
        return {"status": "already_running", "message": "Crawler is already active"}

    _crawler_state["running"] = True
    _crawler_state["last_check"] = datetime.now(timezone.utc).isoformat()
    _crawler_state["packages_checked"] = 0
    _crawler_state["threats_found"] = 0

    # In a real deployment we'd schedule a Celery task or asyncio.create_task
    # that polls the registries on a loop.  For now we just flip the flag.
    logger.info("Registry crawler started")
    return {"status": "started", "message": "Registry crawler started successfully"}


@router.post("/stop")
async def stop_crawler(_: dict = Depends(get_current_user)):
    if not _crawler_state["running"]:
        return {"status": "not_running", "message": "Crawler is not active"}

    _crawler_state["running"] = False
    logger.info("Registry crawler stopped")
    return {"status": "stopped", "message": "Registry crawler stopped successfully"}


@router.get("/status")
async def crawler_status(_: dict = Depends(get_current_user)):
    return {
        "running": _crawler_state["running"],
        "last_check": _crawler_state["last_check"],
        "packages_checked": _crawler_state["packages_checked"],
        "threats_found": _crawler_state["threats_found"],
    }
