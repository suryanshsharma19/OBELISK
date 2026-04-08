#!/usr/bin/env python3
"""Automated training/evaluation/release pipeline for OBELISK models."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_step(label: str, cmd: list[str]) -> None:
    print(f"\\n=== {label} ===")
    print("$ " + " ".join(cmd))
    subprocess.run(cmd, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OBELISK ML pipeline")
    parser.add_argument("--python", default=sys.executable, help="Python interpreter for subcommands")
    parser.add_argument("--skip-train", action="store_true")
    parser.add_argument("--skip-benchmark", action="store_true")
    parser.add_argument("--skip-gates", action="store_true")
    parser.add_argument("--skip-version", action="store_true")
    parser.add_argument("--benchmark-json", default="backend/ml_models/saved_models/realistic_leaderboard.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    train_dir = Path(__file__).resolve().parent

    if not args.skip_train:
        run_step(
            "Train models",
            [args.python, str(train_dir / "train_all_real.py")],
        )

    if not args.skip_benchmark:
        run_step(
            "Benchmark models",
            [args.python, str(train_dir / "realistic_benchmark.py")],
        )

    if not args.skip_gates:
        run_step(
            "Check model acceptance gates",
            [
                args.python,
                str(train_dir / "check_model_gates.py"),
                "--benchmark",
                args.benchmark_json,
            ],
        )

    if not args.skip_version:
        run_step(
            "Version model artifacts",
            [
                args.python,
                str(train_dir / "version_artifacts.py"),
                "--benchmark-json",
                args.benchmark_json,
            ],
        )

    print("\\nPipeline completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
