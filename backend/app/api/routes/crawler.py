"""Crawler control routes - start/stop/status for the registry monitor."""

import asyncio
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_user
from app.config import get_settings
from app.core.logging import setup_logger

logger = setup_logger(__name__)
settings = get_settings()

router = APIRouter()


class CrawlerStartRequest(BaseModel):
    registry: Literal["npm", "pypi", "all"] = "all"
    interval_seconds: int | None = Field(default=None, ge=5, le=86_400)

# in-memory crawler state
_crawler_state: dict[str, Any] = {
    "running": False,
    "task": None,
    "last_check": None,
    "packages_checked": 0,
    "threats_found": 0,
    "registry": "all",
    "interval_seconds": settings.crawler_poll_interval_seconds,
    "last_error": None,
    "last_cycle_result": {},
}


def get_crawler_snapshot() -> dict[str, Any]:
    checked = int(_crawler_state.get("packages_checked", 0) or 0)
    running = bool(_crawler_state.get("running", False))

    return {
        "running": running,
        "is_running": running,
        "last_check": _crawler_state.get("last_check"),
        "packages_checked": checked,
        "packages_scanned": checked,
        "threats_found": int(_crawler_state.get("threats_found", 0) or 0),
        "registry": _crawler_state.get("registry", "all"),
        "interval_seconds": int(_crawler_state.get("interval_seconds", settings.crawler_poll_interval_seconds)),
        "last_error": _crawler_state.get("last_error"),
        "last_cycle_result": _crawler_state.get("last_cycle_result", {}),
    }


async def _run_crawler_cycle() -> dict[str, Any]:
    from app.workers.tasks import crawl_registry_task

    selected_registry = str(_crawler_state.get("registry", "all"))
    registries = [selected_registry] if selected_registry in {"npm", "pypi"} else ["npm", "pypi"]
    cycle_result: dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "results": [],
    }

    for registry in registries:
        batch_size = settings.crawler_batch_size_npm if registry == "npm" else settings.crawler_batch_size_pypi
        result = await asyncio.to_thread(
            crawl_registry_task,
            registry=registry,
            batch_size=batch_size,
        )

        if isinstance(result, dict):
            cycle_result["results"].append(result)
            scanned = int(result.get("candidates", result.get("queued", 0)) or 0)
            _crawler_state["packages_checked"] += scanned
            _crawler_state["threats_found"] += int(result.get("threats_found", 0) or 0)

    cycle_result["finished_at"] = datetime.now(timezone.utc).isoformat()
    return cycle_result


async def _crawler_loop() -> None:
    logger.info("Crawler loop started")
    first_cycle = True
    try:
        while _crawler_state.get("running", False):
            if first_cycle:
                first_cycle = False
                await asyncio.sleep(1)
                if not _crawler_state.get("running", False):
                    break

            _crawler_state["last_error"] = None
            _crawler_state["last_cycle_result"] = await _run_crawler_cycle()
            _crawler_state["last_check"] = datetime.now(timezone.utc).isoformat()

            interval = int(_crawler_state.get("interval_seconds", settings.crawler_poll_interval_seconds))
            await asyncio.sleep(max(interval, 5))
    except asyncio.CancelledError:
        logger.info("Crawler loop cancelled")
        raise
    except Exception as exc:
        _crawler_state["last_error"] = str(exc)
        logger.error("Crawler loop failed: %s", exc)
    finally:
        _crawler_state["task"] = None
        logger.info("Crawler loop stopped")


@router.post("/start")
async def start_crawler(
    payload: CrawlerStartRequest = Body(default_factory=CrawlerStartRequest),
    _: dict = Depends(get_current_user),
):
    if _crawler_state["running"]:
        return {"status": "already_running", "message": "Crawler is already active"}

    _crawler_state["registry"] = payload.registry
    _crawler_state["interval_seconds"] = payload.interval_seconds or settings.crawler_poll_interval_seconds
    _crawler_state["running"] = True
    _crawler_state["last_check"] = datetime.now(timezone.utc).isoformat()
    _crawler_state["packages_checked"] = 0
    _crawler_state["threats_found"] = 0
    _crawler_state["last_error"] = None
    _crawler_state["last_cycle_result"] = {}

    _crawler_state["task"] = asyncio.create_task(_crawler_loop(), name="obelisk-crawler-loop")

    logger.info("Registry crawler started")
    return {
        "status": "started",
        "message": "Registry crawler started successfully",
        "crawler": get_crawler_snapshot(),
    }


@router.post("/stop")
async def stop_crawler(_: dict = Depends(get_current_user)):
    if not _crawler_state["running"]:
        return {"status": "not_running", "message": "Crawler is not active"}

    _crawler_state["running"] = False
    task: asyncio.Task | None = _crawler_state.get("task")
    if task and not task.done():
        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=0.25)
        except asyncio.CancelledError:
            pass
        except asyncio.TimeoutError:
            logger.warning("Crawler task did not cancel immediately; detaching task")
    _crawler_state["task"] = None

    logger.info("Registry crawler stopped")
    return {
        "status": "stopped",
        "message": "Registry crawler stopped successfully",
        "crawler": get_crawler_snapshot(),
    }


@router.get("/status")
async def crawler_status(_: dict = Depends(get_current_user)):
    return get_crawler_snapshot()
