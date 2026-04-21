"""Sandbox service - isolated package execution for behavioural analysis."""

from __future__ import annotations

import asyncio
import base64
import json
import time
from typing import Any

from app.config import get_settings
from app.core.logging import setup_logger

logger = setup_logger(__name__)
settings = get_settings()


async def run_in_sandbox(
    package_name: str,
    version: str,
    registry: str = "npm",
    code: str = "",
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
        return await _docker_sandbox(package_name, version, registry, code=code)

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
    code: str,
) -> dict[str, Any]:
    started = time.perf_counter()
    image = "node:18-alpine" if registry == "npm" else "python:3.11-alpine"

    cmd = ["docker", "run", "--rm", "--network=none", f"--memory={settings.sandbox_memory_limit}", "--cpus=0.5"]

    if code.strip():
        encoded = base64.b64encode(code.encode("utf-8")).decode("ascii")
        cmd.extend([
            "-e", f"OBELISK_CODE_B64={encoded}",
            "-e", f"OBELISK_RELEASE_TRACK={settings.sandbox_release_track}",
            image,
        ])
        if registry == "npm":
            cmd.extend(["node", "-e", _node_instrumentation_script()])
        else:
            cmd.extend(["python", "-c", _python_instrumentation_script()])
    else:
        install_cmd = (
            f"npm install {package_name}@{version} --ignore-scripts"
            if registry == "npm"
            else f"pip install --no-input {package_name}=={version}"
        )
        cmd.extend([
            image,
            "sh",
            "-lc",
            install_cmd,
        ])

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
        elapsed = round(time.perf_counter() - started, 3)

        if code.strip():
            parsed = _parse_instrumentation_output(stdout.decode(errors="replace"))
            parsed.update(
                {
                    "exit_code": int(parsed.get("exit_code", proc.returncode) or proc.returncode),
                    "execution_time_s": elapsed,
                    "mode": "docker",
                    "enabled": True,
                    "release_track": settings.sandbox_release_track,
                }
            )
            if stderr:
                logs = list(parsed.get("logs", []))
                logs.append(stderr.decode(errors="replace")[:500])
                parsed["logs"] = logs[:25]
            return parsed

        return {
            "network_attempts": 0,
            "file_writes": 0,
            "cpu_usage_percent": 0.0,
            "memory_usage_mb": 0.0,
            "process_spawns": 0,
            "exit_code": proc.returncode,
            "execution_time_s": elapsed,
            "stdout": stdout.decode(errors="replace")[:5000],
            "stderr": stderr.decode(errors="replace")[:5000],
            "mode": "docker",
            "enabled": True,
            "release_track": settings.sandbox_release_track,
            "reason": "Docker sandbox package operation completed",
            "logs": [],
        }
    except asyncio.TimeoutError:
        logger.warning("Sandbox timed out for %s", package_name)
        return {
            "network_attempts": 0,
            "file_writes": 0,
            "cpu_usage_percent": 0.0,
            "memory_usage_mb": 0.0,
            "process_spawns": 0,
            "exit_code": -1,
            "execution_time_s": round(time.perf_counter() - started, 3),
            "mode": "docker",
            "enabled": True,
            "release_track": settings.sandbox_release_track,
            "reason": "Docker sandbox timed out",
            "error": "timeout",
            "logs": [],
        }
    except Exception as exc:
        logger.error("Sandbox execution failed: %s", exc)
        return {
            "network_attempts": 0,
            "file_writes": 0,
            "cpu_usage_percent": 0.0,
            "memory_usage_mb": 0.0,
            "process_spawns": 0,
            "exit_code": -1,
            "execution_time_s": round(time.perf_counter() - started, 3),
            "mode": "docker",
            "enabled": True,
            "release_track": settings.sandbox_release_track,
            "reason": "Docker sandbox failed",
            "error": str(exc),
            "logs": [],
        }


def _parse_instrumentation_output(stdout: str) -> dict[str, Any]:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            parsed = json.loads(line)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue

    return {
        "network_attempts": 0,
        "file_writes": 0,
        "cpu_usage_percent": 0.0,
        "memory_usage_mb": 0.0,
        "process_spawns": 0,
        "exit_code": -1,
        "logs": ["Sandbox instrumentation did not produce JSON output"],
        "reason": "Sandbox instrumentation parse failure",
    }


def _node_instrumentation_script() -> str:
    return r'''
const vm = require('vm');
const code = Buffer.from(process.env.OBELISK_CODE_B64 || '', 'base64').toString('utf8');
const metrics = { network_attempts: 0, file_writes: 0, process_spawns: 0, logs: [] };

const child_process = {
  exec: () => { metrics.process_spawns += 1; metrics.logs.push('child_process.exec'); return { pid: 0, on: () => {} }; },
  execSync: () => { metrics.process_spawns += 1; metrics.logs.push('child_process.execSync'); return Buffer.from(''); },
  spawn: () => { metrics.process_spawns += 1; metrics.logs.push('child_process.spawn'); return { pid: 0, on: () => {} }; },
  spawnSync: () => { metrics.process_spawns += 1; metrics.logs.push('child_process.spawnSync'); return { status: 0 }; }
};

const fs = {
  writeFile: () => { metrics.file_writes += 1; metrics.logs.push('fs.writeFile'); },
  writeFileSync: () => { metrics.file_writes += 1; metrics.logs.push('fs.writeFileSync'); },
  appendFile: () => { metrics.file_writes += 1; metrics.logs.push('fs.appendFile'); },
  appendFileSync: () => { metrics.file_writes += 1; metrics.logs.push('fs.appendFileSync'); }
};

const netmod = {
  request: () => { metrics.network_attempts += 1; throw new Error('network blocked'); },
  get: () => { metrics.network_attempts += 1; throw new Error('network blocked'); }
};

function obeliskRequire(name) {
  if (name === 'child_process') return child_process;
  if (name === 'fs') return fs;
  if (name === 'http' || name === 'https' || name === 'net' || name === 'dns') return netmod;
  return require(name);
}

const context = {
  require: obeliskRequire,
  console,
  Buffer,
  process: { env: {}, argv: [], stdout: { write: () => {} }, stderr: { write: () => {} } },
  module: { exports: {} },
  exports: {},
  setTimeout,
  clearTimeout,
  setInterval,
  clearInterval,
};

let exitCode = 0;
try {
  vm.runInNewContext(code, context, { timeout: 2500 });
} catch (err) {
  exitCode = 1;
  metrics.logs.push(String((err && err.message) ? err.message : err));
}

console.log(JSON.stringify({
  network_attempts: metrics.network_attempts,
  file_writes: metrics.file_writes,
  cpu_usage_percent: 0.0,
  memory_usage_mb: 0.0,
  process_spawns: metrics.process_spawns,
  exit_code: exitCode,
  execution_time_s: 0.0,
  mode: 'docker',
  enabled: true,
  reason: 'Docker sandbox code instrumentation run',
  release_track: process.env.OBELISK_RELEASE_TRACK || 'v1.1',
  logs: metrics.logs.slice(0, 25)
}));
'''


def _python_instrumentation_script() -> str:
    return r'''
import base64
import builtins
import json
import os
import subprocess

code = base64.b64decode(os.environ.get("OBELISK_CODE_B64", "").encode("utf-8")).decode("utf-8", errors="replace")
metrics = {"network_attempts": 0, "file_writes": 0, "process_spawns": 0, "logs": []}

def _count_spawn(*args, **kwargs):
    metrics["process_spawns"] += 1
    metrics["logs"].append("subprocess")
    class _Proc:
        returncode = 0
        def communicate(self, *a, **k):
            return (b"", b"")
    return _Proc()

def _count_os_system(*args, **kwargs):
    metrics["process_spawns"] += 1
    metrics["logs"].append("os.system")
    return 0

def _open_wrapper(file, mode="r", *args, **kwargs):
    if any(flag in mode for flag in ("w", "a", "x", "+")):
        metrics["file_writes"] += 1
        metrics["logs"].append("file_write")
    raise RuntimeError("file write blocked")

subprocess.Popen = _count_spawn
subprocess.run = _count_spawn
subprocess.call = lambda *a, **k: 0
os.system = _count_os_system
builtins.open = _open_wrapper

exit_code = 0
try:
    exec(code, {"__name__": "__main__"}, {})
except Exception as exc:
    exit_code = 1
    metrics["logs"].append(str(exc))

print(json.dumps({
    "network_attempts": metrics["network_attempts"],
    "file_writes": metrics["file_writes"],
    "cpu_usage_percent": 0.0,
    "memory_usage_mb": 0.0,
    "process_spawns": metrics["process_spawns"],
    "exit_code": exit_code,
    "execution_time_s": 0.0,
    "mode": "docker",
    "enabled": True,
    "reason": "Docker sandbox code instrumentation run",
    "release_track": os.environ.get("OBELISK_RELEASE_TRACK", "v1.1"),
    "logs": metrics["logs"][:25],
}))
'''
