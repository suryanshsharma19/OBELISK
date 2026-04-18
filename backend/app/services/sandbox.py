"""Sandbox service - isolated package execution for behavioural analysis."""

from __future__ import annotations

import asyncio
from typing import Any

from app.config import get_settings
from app.core.logging import setup_logger

logger = setup_logger(__name__)
settings = get_settings()


async def run_in_sandbox(
    package_name: str,
    version: str,
    registry: str = "npm",
) -> dict[str, Any]:
    if not settings.sandbox_enabled:
        logger.info(
            "Sandbox disabled for current release; scoped to %s and excluded from critical scoring flow",
            settings.sandbox_release_track,
        )
        return {
            "network_attempts": 0,
            "file_writes": 0,
            "cpu_usage_percent": 0.0,
            "memory_usage_mb": 0.0,
            "process_spawns": 0,
            "exit_code": 0,
            "execution_time_s": 0.0,
            "mode": "disabled",
            "logs": [],
            "enabled": False,
            "release_track": settings.sandbox_release_track,
            "reason": "Sandbox is scoped to v1.1 and not part of current critical scoring",
        }

    if settings.sandbox_allow_docker:
        logger.info("Sandbox (docker): %s@%s registry=%s", package_name, version, registry)
        return await _docker_sandbox(package_name, version, registry)

    logger.info(
        "Sandbox (sim): %s@%s registry=%s",
        package_name, version, registry,
    )
    return await _simulate_sandbox(package_name, version, registry)


async def _simulate_sandbox(
    package_name: str,
    version: str,
    registry: str,
) -> dict[str, Any]:
    # simulate some processing time
    await asyncio.sleep(0.05)

    return {
        "network_attempts": 0,
        "file_writes": 0,
        "cpu_usage_percent": 2.1,
        "memory_usage_mb": 24.5,
        "process_spawns": 0,
        "exit_code": 0,
        "execution_time_s": 0.05,
        "mode": "simulation",
        "enabled": True,
        "release_track": settings.sandbox_release_track,
        "reason": "Sandbox docker execution is disabled; using simulation telemetry",
        "logs": [],
    }


async def _docker_sandbox(
    package_name: str,
    version: str,
    registry: str,
) -> dict[str, Any]:
    # real Docker sandbox - enable once Docker-in-Docker is set up
    image = "node:18-alpine" if registry == "npm" else "python:3.11-alpine"
    install_cmd = (
        f"npm install {package_name}@{version}"
        if registry == "npm"
        else f"pip install {package_name}=={version}"
    )

    cmd = [
        "docker", "run", "--rm",
        "--network=none",
        f"--memory={settings.sandbox_memory_limit}",
        "--cpus=0.5",
        f"--stop-timeout={settings.sandbox_timeout}",
        image,
        "sh", "-c", install_cmd,
    ]

    logger.info("Sandbox docker cmd: %s", " ".join(cmd))

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=settings.sandbox_timeout,
        )
        return {
            "exit_code": proc.returncode,
            "stdout": stdout.decode(errors="replace")[:5000],
            "stderr": stderr.decode(errors="replace")[:5000],
            "mode": "docker",
            "enabled": True,
            "release_track": settings.sandbox_release_track,
            "reason": "Docker sandbox execution completed",
        }
    except asyncio.TimeoutError:
        logger.warning("Sandbox timed out for %s", package_name)
        return {
            "exit_code": -1,
            "mode": "docker",
            "enabled": True,
            "release_track": settings.sandbox_release_track,
            "reason": "Docker sandbox timed out",
            "error": "timeout",
        }
    except Exception as exc:
        logger.error("Sandbox execution failed: %s", exc)
        return {
            "exit_code": -1,
            "mode": "docker",
            "enabled": True,
            "release_track": settings.sandbox_release_track,
            "reason": "Docker sandbox failed",
            "error": str(exc),
        }
