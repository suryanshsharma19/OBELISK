"""App-wide constants and enums."""

from __future__ import annotations

from enum import Enum
from typing import Final


class ThreatLevel(str, Enum):
    SAFE = "safe"          # 0–20
    LOW = "low"            # 20–40
    MEDIUM = "medium"      # 40–60
    HIGH = "high"          # 60–80
    CRITICAL = "critical"  # 80–100


THREAT_LEVEL_RANGES: Final[dict[ThreatLevel, tuple[int, int]]] = {
    ThreatLevel.SAFE: (0, 20),
    ThreatLevel.LOW: (20, 40),
    ThreatLevel.MEDIUM: (40, 60),
    ThreatLevel.HIGH: (60, 80),
    ThreatLevel.CRITICAL: (80, 100),
}


def score_to_threat_level(score: float) -> ThreatLevel:
    if score < 0 or score > 100:
        raise ValueError(f"Score must be 0–100, got {score}")
    for level, (low, high) in THREAT_LEVEL_RANGES.items():
        if low <= score < high:
            return level
    return ThreatLevel.CRITICAL


REGISTRY_TYPES: Final[list[str]] = ["npm", "pypi"]

DETECTION_WEIGHTS: Final[dict[str, float]] = {
    "typosquatting": 0.25,
    "code_analysis": 0.35,
    "behavior": 0.15,
    "maintainer": 0.15,
    "dependency": 0.10,
}

POPULAR_PACKAGES: Final[list[str]] = [
    "express", "react", "lodash", "axios", "moment",
    "chalk", "commander", "debug", "request", "bluebird",
    "async", "underscore", "uuid", "minimist", "glob",
    "mkdirp", "yargs", "semver", "fs-extra", "inquirer",
    "dotenv", "body-parser", "webpack", "typescript", "prop-types",
    "classnames", "react-dom", "jquery", "rxjs", "tslib",
    "core-js", "ws", "supports-color", "colors", "cheerio",
    "eslint", "babel-core", "next", "vue", "angular",
    "mongoose", "redis", "pg", "mysql", "nodemon",
    "jest", "mocha", "prettier", "eslint-plugin-react", "socket.io",
]

SUSPICIOUS_CODE_PATTERNS: Final[list[str]] = [
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\bsubprocess\.\w+\s*\(",
    r"\bos\.system\s*\(",
    r"\bos\.popen\s*\(",
    r"\bbase64\.b64decode\s*\(",
    r"\batob\s*\(",
    r"\brequests\.\w+\s*\(",
    r"\burllib\.request\.\w+\s*\(",
    r"\bhttp\.get\s*\(",
    r"\bhttp\.request\s*\(",
    r"\bfetch\s*\(",
    r"\b__import__\s*\(",
    r"\bimportlib\.import_module\s*\(",
    r"\bfs\.writeFileSync\s*\(",
    r"\bchild_process\.\w+\s*\(",
]
