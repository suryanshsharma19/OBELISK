"""Application constants for OBELISK - Supply Chain Attack Detector."""

from __future__ import annotations

from enum import Enum
from typing import Final


# ---------------------------------------------------------------------------
# 1. Threat Levels
# ---------------------------------------------------------------------------

class ThreatLevel(str, Enum):
    """Risk classification mapped to numeric score ranges."""

    SAFE = "SAFE"          # 0–20
    LOW = "LOW"            # 20–40
    MEDIUM = "MEDIUM"      # 40–60
    HIGH = "HIGH"          # 60–80
    CRITICAL = "CRITICAL"  # 80–100


THREAT_LEVEL_RANGES: Final[dict[ThreatLevel, tuple[int, int]]] = {
    ThreatLevel.SAFE: (0, 20),
    ThreatLevel.LOW: (20, 40),
    ThreatLevel.MEDIUM: (40, 60),
    ThreatLevel.HIGH: (60, 80),
    ThreatLevel.CRITICAL: (80, 100),
}


def score_to_threat_level(score: float) -> ThreatLevel:
    """Map a numeric risk score (0–100) to a ``ThreatLevel``."""
    if score < 0 or score > 100:
        raise ValueError(f"Score must be 0–100, got {score}")
    for level, (low, high) in THREAT_LEVEL_RANGES.items():
        if low <= score < high:
            return level
    return ThreatLevel.CRITICAL  # score == 100


# ---------------------------------------------------------------------------
# 2. Supported Registries
# ---------------------------------------------------------------------------

REGISTRY_TYPES: Final[list[str]] = ["npm", "pypi"]


# ---------------------------------------------------------------------------
# 3. Detection Model Weights for Risk Scoring
# ---------------------------------------------------------------------------

DETECTION_WEIGHTS: Final[dict[str, float]] = {
    "typosquatting": 0.25,
    "code_analysis": 0.35,
    "behavior": 0.15,
    "maintainer": 0.15,
    "dependency": 0.10,
}


# ---------------------------------------------------------------------------
# 4. Popular Packages (top 50 npm — typosquatting reference list)
# ---------------------------------------------------------------------------

POPULAR_PACKAGES: Final[list[str]] = [
    "express",
    "react",
    "lodash",
    "axios",
    "moment",
    "chalk",
    "commander",
    "debug",
    "request",
    "bluebird",
    "async",
    "underscore",
    "uuid",
    "minimist",
    "glob",
    "mkdirp",
    "yargs",
    "semver",
    "fs-extra",
    "inquirer",
    "dotenv",
    "body-parser",
    "webpack",
    "typescript",
    "prop-types",
    "classnames",
    "react-dom",
    "jquery",
    "rxjs",
    "tslib",
    "core-js",
    "ws",
    "supports-color",
    "colors",
    "cheerio",
    "eslint",
    "babel-core",
    "next",
    "vue",
    "angular",
    "mongoose",
    "redis",
    "pg",
    "mysql",
    "nodemon",
    "jest",
    "mocha",
    "prettier",
    "eslint-plugin-react",
    "socket.io",
]


# ---------------------------------------------------------------------------
# 5. Suspicious Code Patterns (regex strings for code analysis)
# ---------------------------------------------------------------------------

SUSPICIOUS_CODE_PATTERNS: Final[list[str]] = [
    # eval / exec usage
    r"\beval\s*\(",
    r"\bexec\s*\(",
    # subprocess calls
    r"\bsubprocess\.\w+\s*\(",
    # os.system / os.popen
    r"\bos\.system\s*\(",
    r"\bos\.popen\s*\(",
    # base64 decoding
    r"\bbase64\.b64decode\s*\(",
    r"\batob\s*\(",
    # network requests
    r"\brequests\.\w+\s*\(",
    r"\burllib\.request\.\w+\s*\(",
    r"\bhttp\.get\s*\(",
    r"\bhttp\.request\s*\(",
    r"\bfetch\s*\(",
    # dynamic imports / code loading
    r"\b__import__\s*\(",
    r"\bimportlib\.import_module\s*\(",
    # file system writes in install scripts
    r"\bfs\.writeFileSync\s*\(",
    r"\bchild_process\.\w+\s*\(",
]
