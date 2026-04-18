"""WebSocket endpoint for real-time event streaming."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import func

from app.config import get_settings
from app.core.auth import safe_decode_access_token
from app.core.logging import setup_logger

logger = setup_logger(__name__)
settings = get_settings()
router = APIRouter()


class ConnectionManager:
    """Tracks active WebSocket connections."""

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)
        logger.info("WebSocket client connected (%d total)", len(self._connections))

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.remove(websocket)
        logger.info("WebSocket client disconnected (%d remaining)", len(self._connections))

    async def broadcast(self, event_type: str, payload: dict[str, Any]) -> None:
        message = json.dumps({"type": event_type, "data": payload})
        dead: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections.remove(ws)


# singleton so services can import and broadcast
manager = ConnectionManager()


def _build_stats_snapshot() -> dict[str, Any]:
    from app.db.models import Alert, Package
    from app.db.session import SessionLocal

    total_packages = 0
    malicious_packages = 0
    active_alerts = 0

    db = None
    try:
        db = SessionLocal()
        total_packages = db.query(func.count(Package.id)).scalar() or 0
        malicious_packages = (
            db.query(func.count(Package.id)).filter(Package.is_malicious == True).scalar()
        ) or 0
        active_alerts = (
            db.query(func.count(Alert.id)).filter(Alert.is_resolved == False).scalar()
        ) or 0
    except Exception as exc:
        logger.debug("Stats snapshot fallback due to DB error: %s", exc)
    finally:
        if db is not None:
            db.close()

    crawler = {}
    try:
        from app.api.routes.crawler import get_crawler_snapshot

        crawler = get_crawler_snapshot()
    except Exception:
        crawler = {}

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_packages": int(total_packages),
        "malicious_packages": int(malicious_packages),
        "active_alerts": int(active_alerts),
        "crawler": crawler,
    }


async def _periodic_stats_sender(websocket: WebSocket) -> None:
    interval = max(int(settings.ws_stats_interval_seconds), 5)
    while True:
        await asyncio.sleep(interval)
        payload = await asyncio.to_thread(_build_stats_snapshot)
        await websocket.send_text(json.dumps({"type": "stats_update", "data": payload}))


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    auth_header = websocket.headers.get("authorization", "")
    if not token and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()

    payload = safe_decode_access_token(token) if token else None
    if payload is None:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket)
    periodic_task = asyncio.create_task(_periodic_stats_sender(websocket))
    try:
        while True:
            # Keep connection alive — wait for client messages
            # (or heartbeat pings handled by the protocol layer)
            data = await websocket.receive_text()
            message_type = ""
            if data == "ping":
                message_type = "ping"
            else:
                try:
                    payload = json.loads(data)
                    if isinstance(payload, dict):
                        message_type = str(payload.get("type", ""))
                except Exception:
                    message_type = ""

            # Clients can send ping as plain text or JSON payload.
            if message_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
    finally:
        periodic_task.cancel()
        try:
            await periodic_task
        except asyncio.CancelledError:
            pass
