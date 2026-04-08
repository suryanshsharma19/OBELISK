#!/usr/bin/env python3
"""Create versioned release manifests for trained model artifacts.

This does not copy large binaries by default; it snapshots metadata and
cryptographic hashes so releases remain reproducible and auditable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Version OBELISK model artifacts")
    parser.add_argument(
        "--saved-models-root",
        default="backend/ml_models/saved_models",
        help="Root directory for saved models",
    )
    parser.add_argument(
        "--benchmark-json",
        default="backend/ml_models/saved_models/realistic_leaderboard.json",
        help="Benchmark summary to include in manifest",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.saved_models_root)

    release_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    release_dir = root / "releases" / release_id
    release_dir.mkdir(parents=True, exist_ok=True)

    # Canonical artifacts used by runtime defaults and best candidates.
    tracked_files = [
        root / "codebert_best" / "model.safetensors",
        root / "codebert_best" / "config.json",
        root / "codebert_best" / "tokenizer.json",
        root / "gnn_best" / "model.pt",
        root / "isolation_forest_best_realistic" / "model.joblib",
        root / "isolation_forest_best_realistic" / "scaler.joblib",
        root / "isolation_forest_best_realistic" / "metadata.joblib",
    ]

    artifacts = []
    for file_path in tracked_files:
        if not file_path.exists():
            artifacts.append(
                {
                    "path": str(file_path),
                    "exists": False,
                }
            )
            continue

        artifacts.append(
            {
                "path": str(file_path),
                "exists": True,
                "size_bytes": file_path.stat().st_size,
                "sha256": sha256_file(file_path),
            }
        )

    manifest = {
        "release_id": release_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "benchmark_json": str(Path(args.benchmark_json)),
        "artifacts": artifacts,
    }

    manifest_path = release_dir / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    latest_path = root / "releases" / "latest.json"
    with latest_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    print(f"Created artifact manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
