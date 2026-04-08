#!/usr/bin/env python3
"""Benchmark the /api/packages/analyze endpoint.

Modes:
- live: benchmark an already-running backend over HTTP.
- stub: benchmark API overhead with in-process TestClient and a stubbed analyzer.
"""

from __future__ import annotations

import argparse
import asyncio
from contextlib import asynccontextmanager
import os
import sys
import statistics
import time
from pathlib import Path
from typing import Any

import httpx

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    values = sorted(values)
    idx = (len(values) - 1) * q
    lo = int(idx)
    hi = min(lo + 1, len(values) - 1)
    frac = idx - lo
    return values[lo] * (1.0 - frac) + values[hi] * frac


async def login(base_url: str, username: str, password: str, timeout: float) -> str:
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            f"{base_url}/api/auth/login",
            json={"username": username, "password": password},
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


async def run_live_benchmark(args: argparse.Namespace) -> dict[str, float]:
    token = await login(args.base_url, args.username, args.password, args.timeout)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": args.package_name,
        "version": args.package_version,
        "registry": args.registry,
        "code": args.code,
    }

    latencies_ms: list[float] = []

    async with httpx.AsyncClient(timeout=args.timeout) as client:
        # Warmup requests
        for _ in range(args.warmup):
            await client.post(f"{args.base_url}/api/packages/analyze", json=payload, headers=headers)

        # Measured requests
        for _ in range(args.samples):
            t0 = time.perf_counter()
            resp = await client.post(f"{args.base_url}/api/packages/analyze", json=payload, headers=headers)
            resp.raise_for_status()
            latencies_ms.append((time.perf_counter() - t0) * 1000.0)

    return {
        "p50_ms": percentile(latencies_ms, 0.50),
        "p95_ms": percentile(latencies_ms, 0.95),
        "p99_ms": percentile(latencies_ms, 0.99),
        "avg_ms": statistics.mean(latencies_ms),
        "samples": float(len(latencies_ms)),
    }


def run_stub_benchmark(args: argparse.Namespace) -> dict[str, float]:
    from fastapi.testclient import TestClient

    from app.api.dependencies import get_current_user
    from app.main import app
    from app.services import analysis_service

    async def _stub_analyze_package(**kwargs: Any) -> dict[str, Any]:
        return {
            "package": {
                "name": kwargs["name"],
                "version": kwargs["version"],
                "registry": kwargs["registry"],
                "risk_score": 12.34,
                "threat_level": "low",
                "is_malicious": False,
            },
            "analysis": {
                "risk_score": 12.34,
                "threat_level": "low",
                "is_malicious": False,
                "confidence": 0.9,
            },
            "detection_details": {},
        }

    original = analysis_service.analyze_package
    original_lifespan_context = app.router.lifespan_context

    @asynccontextmanager
    async def _noop_lifespan(_app: Any):
        yield

    app.router.lifespan_context = _noop_lifespan
    analysis_service.analyze_package = _stub_analyze_package
    app.dependency_overrides[get_current_user] = lambda: {"sub": "benchmark-user"}

    latencies_ms: list[float] = []
    payload = {
        "name": args.package_name,
        "version": args.package_version,
        "registry": args.registry,
        "code": args.code,
    }

    try:
        with TestClient(app) as client:
            for _ in range(args.warmup):
                client.post("/api/packages/analyze", json=payload)

            for _ in range(args.samples):
                t0 = time.perf_counter()
                resp = client.post("/api/packages/analyze", json=payload)
                assert resp.status_code == 200
                latencies_ms.append((time.perf_counter() - t0) * 1000.0)
    finally:
        analysis_service.analyze_package = original
        app.router.lifespan_context = original_lifespan_context
        app.dependency_overrides.clear()

    return {
        "p50_ms": percentile(latencies_ms, 0.50),
        "p95_ms": percentile(latencies_ms, 0.95),
        "p99_ms": percentile(latencies_ms, 0.99),
        "avg_ms": statistics.mean(latencies_ms),
        "samples": float(len(latencies_ms)),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark /api/packages/analyze")
    parser.add_argument("--mode", choices=["live", "stub"], default="live")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--username", default=os.getenv("AUTH_USERNAME", "admin"))
    parser.add_argument("--password", default=os.getenv("AUTH_PASSWORD", "change_me"))
    parser.add_argument("--package-name", default="express")
    parser.add_argument("--package-version", default="4.18.2")
    parser.add_argument("--registry", default="npm")
    parser.add_argument("--code", default="module.exports = function add(a,b){return a+b;}")
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--enforce-under-ms", type=float, default=1000.0)
    return parser.parse_args()


async def main() -> int:
    args = parse_args()

    if args.mode == "live":
        metrics = await run_live_benchmark(args)
    else:
        metrics = run_stub_benchmark(args)

    print(f"mode={args.mode} samples={int(metrics['samples'])}")
    print(
        f"latency_ms p50={metrics['p50_ms']:.2f} p95={metrics['p95_ms']:.2f} "
        f"p99={metrics['p99_ms']:.2f} avg={metrics['avg_ms']:.2f}"
    )

    if metrics["p95_ms"] > args.enforce_under_ms:
        print(
            f"FAIL: p95 latency {metrics['p95_ms']:.2f}ms exceeds "
            f"target {args.enforce_under_ms:.2f}ms"
        )
        return 2

    print("PASS: /api/packages/analyze meets latency target")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
