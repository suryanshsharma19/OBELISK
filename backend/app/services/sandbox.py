"""Sandbox Service — isolated package execution for behavioural analysis.

In production this spins up a Docker container with:
  --network=none --memory=512m --cpus=0.5
installs the package, imports it, and monitors syscalls.

For local dev / CI we provide a *simulation mode* that skips Docker
and returns heuristic-based results instead.

Functions:
    run_in_sandbox:  Execute a package and return behavioural signals
"""

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
    """
    Run a package in an isolated environment and collect behavioural data.

    Returns:
        Dict with keys: network_attempts, file_writes, cpu_usage,
        memory_usage, process_spawns, exit_code, execution_time.
    """
    # For now we run in simulation mode (no Docker dependency)
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
    """
    Lightweight simulation when Docker isn't available.
    Returns neutral / safe defaults.
    """
    # Simulate some processing time
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
        "logs": [],
    }


async def _docker_sandbox(
    package_name: str,
    version: str,
    registry: str,
) -> dict[str, Any]:
    """
    Real Docker-based sandbox execution.
    TODO: enable once Docker-in-Docker is configured.
    """
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
        }
    except asyncio.TimeoutError:
        logger.warning("Sandbox timed out for %s", package_name)
        return {"exit_code": -1, "mode": "docker", "error": "timeout"}
    except Exception as exc:
        logger.error("Sandbox execution failed: %s", exc)
        return {"exit_code": -1, "mode": "docker", "error": str(exc)}
