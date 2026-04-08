#!/usr/bin/env python3
"""Model acceptance gates for OBELISK.

Fails with non-zero exit code when benchmarked model quality falls under
minimum thresholds defined in model_acceptance_gates.yaml.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate model quality gates")
    parser.add_argument(
        "--gates",
        default=str(Path(__file__).resolve().parent / "model_acceptance_gates.yaml"),
        help="Path to gate configuration yaml",
    )
    parser.add_argument(
        "--benchmark",
        default="backend/ml_models/saved_models/realistic_leaderboard.json",
        help="Path to benchmark summary json",
    )
    return parser.parse_args()


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def main() -> int:
    args = parse_args()
    gates = load_yaml(args.gates)
    benchmark = load_json(args.benchmark)

    thresholds = gates.get("thresholds", {})

    failures: list[str] = []
    print("Model acceptance report")
    print("======================")

    for model_name, model_thresholds in thresholds.items():
        summary = benchmark.get(model_name, {}).get("summary", {})
        if not summary:
            failures.append(f"{model_name}: missing summary in benchmark")
            print(f"[FAIL] {model_name}: no summary found")
            continue

        print(f"\n{model_name}:")
        for metric_name, min_value in model_thresholds.items():
            metric_key = metric_name.replace("_min", "")
            actual = summary.get(metric_key, {}).get("mean")
            if actual is None:
                failures.append(f"{model_name}.{metric_key}: missing metric")
                print(f"  [FAIL] {metric_key}: missing")
                continue

            ok = actual >= float(min_value)
            status = "PASS" if ok else "FAIL"
            print(f"  [{status}] {metric_key}: actual={actual:.4f} threshold={float(min_value):.4f}")
            if not ok:
                failures.append(
                    f"{model_name}.{metric_key}: actual {actual:.4f} < threshold {float(min_value):.4f}"
                )

    if failures:
        print("\nGate failures:")
        for line in failures:
            print(f"- {line}")
        return 2

    print("\nAll model gates passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
