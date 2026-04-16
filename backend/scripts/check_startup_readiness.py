#!/usr/bin/env python3
"""Run startup/runtime readiness checks as a CI gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.readiness import run_startup_readiness_or_raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OBELISK startup readiness checks")
    parser.add_argument("--strict", action="store_true", help="Fail immediately on any readiness error")
    parser.add_argument(
        "--include-dependencies",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include PostgreSQL/Redis/Neo4j connectivity checks",
    )
    parser.add_argument(
        "--require-ready",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Exit non-zero if readiness is degraded",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        report = run_startup_readiness_or_raise(
            strict=args.strict,
            include_dependencies=args.include_dependencies,
        )
    except Exception as exc:
        print(f"FAIL: startup readiness hard failure: {exc}")
        return 2

    print(json.dumps(report, indent=2, sort_keys=True))

    if args.require_ready and not report["ready"]:
        print("FAIL: startup readiness is degraded")
        return 2

    print("PASS: startup readiness checks satisfied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
