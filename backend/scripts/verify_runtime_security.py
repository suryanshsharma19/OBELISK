#!/usr/bin/env python3
"""Verify runtime security baseline configuration for CI/CD hard gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import get_settings
from app.core.readiness import check_security_baseline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate runtime security baseline")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any security baseline check fails.",
    )
    parser.add_argument(
        "--require-non-local",
        action="store_true",
        help="Exit non-zero if ENVIRONMENT resolves to local.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit full report as JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = get_settings()

    if args.require_non_local and settings.environment == "local":
        print("[security-gate] failed: environment must be non-local")
        return 1

    report = check_security_baseline(settings)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"[security-gate] environment={settings.environment} status={report['status']}")
        if report["failures"]:
            for failure in report["failures"]:
                print(f" - {failure}")

    if args.strict and not report["ok"]:
        print("[security-gate] failed: strict mode enabled and baseline is degraded")
        return 1

    print("[security-gate] passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
