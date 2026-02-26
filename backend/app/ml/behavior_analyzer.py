"""
Behavioral Analyzer — monitors package install & import behaviour.

In a real production deployment this would spin up an isolated Docker
container, install the package, and monitor syscalls / network / FS.
Since we can't assume Docker-in-Docker during local dev, this module
provides a *simulation-grade* analysis that scores based on:

  1. Known suspicious behavioural indicators in package metadata
  2. Heuristics derived from the install scripts (preinstall, postinstall)
  3. Import-time side-effect detection via static analysis

Classes:
    BehaviorAnalyzer(BaseDetector)

Usage:
    analyzer = BehaviorAnalyzer()
    result = await analyzer.run(
        package_name="malicious-pkg",
        registry="npm",
        metadata={...},
    )
"""

from __future__ import annotations

import re
from typing import Any

from app.core.logging import setup_logger
from app.ml.base_detector import BaseDetector
from app.models.analysis import DetectionResult

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
    (re.compile(r"\\bexec\\b", re.I), "exec-call", 10),
    (re.compile(r"\\beval\\b", re.I), "eval-call", 10),
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
        """
        Evaluate behavioural risk.

        Keyword Args:
            package_name (str): Name of the package.
            registry (str): 'npm' or 'pypi'.
            metadata (dict): Package metadata from registry API.
            code (str): Optional code string for extra heuristics.

        Returns:
            DetectionResult with behavioural risk score.
        """
        metadata: dict[str, Any] = kwargs.get("metadata", {})
        code: str = kwargs.get("code", "")
        registry: str = kwargs.get("registry", "npm")

        behaviors: list[dict[str, Any]] = []
        score = 0.0

        # --- Check 1: Suspicious lifecycle scripts ---
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

        # --- Check 2: Minified / obfuscated main entry ---
        main_file = metadata.get("main", "")
        if main_file and any(x in str(main_file) for x in [".min.", "bundle", "dist"]):
            behaviors.append({
                "type": "obfuscated_entry",
                "description": "Main entry point appears minified/bundled",
                "severity": "low",
            })
            score += 5

        # --- Check 3: No repository URL (common in throwaway malicious pkgs) ---
        repo = metadata.get("repository", metadata.get("repository_url", ""))
        if not repo:
            behaviors.append({
                "type": "no_repository",
                "description": "Package has no linked source repository",
                "severity": "medium",
            })
            score += 10

        # --- Check 4: Very few or zero dependents but many dependencies ---
        dep_count = len(metadata.get("dependencies", {}))
        if dep_count > 15:
            behaviors.append({
                "type": "excessive_dependencies",
                "description": f"Unusually high dependency count ({dep_count})",
                "severity": "low",
            })
            score += 8

        # --- Check 5: Code-level heuristics (quick static checks) ---
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
            },
        )
