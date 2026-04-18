"""Behavioral analyzer - scores suspicious install/import patterns."""

from __future__ import annotations

import re
from typing import Any

from app.core.logging import setup_logger
from app.ml.base_detector import BaseDetector
from app.models.analysis import DetectionResult
from app.services import sandbox as sandbox_service

logger = setup_logger(__name__)

# Suspicious npm lifecycle scripts
SUSPICIOUS_SCRIPTS = {"preinstall", "postinstall", "preuninstall"}

# Patterns that are red flags in install scripts
INSTALL_SCRIPT_PATTERNS = [
    (re.compile(r"curl\s+.+\|\s*sh", re.I), "pipe-to-shell", 30),
    (re.compile(r"wget\s+.+\|\s*sh", re.I), "wget-pipe-to-shell", 30),
    (re.compile(r"node\s+-e", re.I), "inline-node-eval", 15),
    (re.compile(r"python\s+-c", re.I), "inline-python-exec", 15),
    (re.compile(r"powershell", re.I), "powershell-execution", 20),
    (re.compile(r"\bexec\b", re.I), "exec-call", 10),
    (re.compile(r"\beval\b", re.I), "eval-call", 10),
]


class BehaviorAnalyzer(BaseDetector):
    """Score package based on behavioural heuristics."""

    name = "behavior"
    version = "1.0.0"
    weight = 0.15

    def __init__(self) -> None:
        super().__init__()
        self._is_ready = True

    async def analyze(self, **kwargs: Any) -> DetectionResult:
        package_name: str = kwargs.get("package_name", "")
        version: str = kwargs.get("version", "latest")
        metadata: dict[str, Any] = kwargs.get("metadata", {})
        code: str = kwargs.get("code", "")
        registry: str = kwargs.get("registry", "npm")

        behaviors: list[dict[str, Any]] = []
        score = 0.0

        # Sandbox execution telemetry (network/fs/process/cpu signals)
        sandbox_result: dict[str, Any] | None = None
        try:
            sandbox_result = await sandbox_service.run_in_sandbox(
                package_name=package_name,
                version=version,
                registry=registry,
            )
        except Exception as exc:
            logger.warning("Sandbox execution failed for %s@%s: %s", package_name, version, exc)
            sandbox_result = {"error": str(exc), "enabled": False, "mode": "error"}

        if sandbox_result:
            network_attempts = int(sandbox_result.get("network_attempts", 0) or 0)
            if network_attempts > 0:
                behaviors.append({
                    "type": "network_attempt",
                    "description": f"Attempted {network_attempts} outbound network operation(s)",
                    "severity": "high",
                })
                score += 25

            file_writes = int(sandbox_result.get("file_writes", 0) or 0)
            if file_writes > 0:
                behaviors.append({
                    "type": "file_write_attempt",
                    "description": f"Attempted {file_writes} file write operation(s)",
                    "severity": "medium",
                })
                score += 20

            process_spawns = int(sandbox_result.get("process_spawns", 0) or 0)
            if process_spawns > 0:
                behaviors.append({
                    "type": "process_spawn",
                    "description": f"Spawned {process_spawns} subprocess(es)",
                    "severity": "high",
                })
                score += 25

            cpu_usage = float(sandbox_result.get("cpu_usage_percent", 0.0) or 0.0)
            if cpu_usage > 80.0:
                behaviors.append({
                    "type": "high_cpu_usage",
                    "description": f"High CPU usage observed ({cpu_usage:.1f}%)",
                    "severity": "high",
                })
                score += 30

            if not sandbox_result.get("enabled", True):
                behaviors.append({
                    "type": "sandbox_unavailable",
                    "description": str(sandbox_result.get("reason", "Sandbox unavailable")),
                    "severity": "low",
                })

        # suspicious lifecycle scripts
        scripts = metadata.get("scripts", {})
        if isinstance(scripts, dict):
            for script_name in SUSPICIOUS_SCRIPTS:
                if script_name in scripts:
                    script_body = scripts[script_name]
                    behaviors.append({
                        "type": f"lifecycle_{script_name}",
                        "description": f"Has {script_name} lifecycle hook",
                        "severity": "medium",
                        "detail": str(script_body)[:200],
                    })
                    score += 15

                    # Scan the script body for dangerous commands
                    for pattern, name, weight in INSTALL_SCRIPT_PATTERNS:
                        if pattern.search(str(script_body)):
                            behaviors.append({
                                "type": f"script_pattern_{name}",
                                "description": f"Install script contains: {name}",
                                "severity": "high",
                                "detail": str(script_body)[:200],
                            })
                            score += weight

        # minified / obfuscated entry point
        main_file = metadata.get("main", "")
        if main_file and any(x in str(main_file) for x in [".min.", "bundle", "dist"]):
            behaviors.append({
                "type": "obfuscated_entry",
                "description": "Main entry point appears minified/bundled",
                "severity": "low",
            })
            score += 5

        # no repository link (common in throwaway malicious pkgs)
        repo = metadata.get("repository", metadata.get("repository_url", ""))
        if not repo:
            behaviors.append({
                "type": "no_repository",
                "description": "Package has no linked source repository",
                "severity": "medium",
            })
            score += 10

        # too many dependencies
        dep_count = len(metadata.get("dependencies", {}))
        if dep_count > 15:
            behaviors.append({
                "type": "excessive_dependencies",
                "description": f"Unusually high dependency count ({dep_count})",
                "severity": "low",
            })
            score += 8

        # quick code-level checks
        if code:
            if "Buffer.from" in code and "base64" in code.lower():
                behaviors.append({
                    "type": "base64_buffer",
                    "description": "Base64 buffer manipulation detected",
                    "severity": "medium",
                })
                score += 12
            if "process.env" in code:
                behaviors.append({
                    "type": "env_access",
                    "description": "Accesses environment variables",
                    "severity": "low",
                })
                score += 5

        score = min(score, 100.0)
        confidence = min(0.5 + len(behaviors) * 0.1, 1.0)

        return DetectionResult(
            score=round(score, 2),
            confidence=round(confidence, 3),
            evidence={
                "behaviors_detected": len(behaviors),
                "behaviors": behaviors,
                "registry": registry,
                "sandbox": sandbox_result or {},
            },
        )
