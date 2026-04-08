#!/usr/bin/env python3
"""Concurrent load validation for OBELISK backend endpoints.

This script validates that the backend can sustain high concurrency and reports
latency percentiles plus success-rate.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import statistics
import time
from dataclasses import dataclass

import httpx


@dataclass
class RunStats:
    total: int
    success: int
    failures: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    avg_ms: float


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


async def login(client: httpx.AsyncClient, base_url: str, username: str, password: str) -> str:
    resp = await client.post(
        f"{base_url}/api/auth/login",
        json={"username": username, "password": password},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


async def run_load(
    base_url: str,
    endpoint: str,
    total_requests: int,
    concurrency: int,
    token: str | None,
    timeout: float,
) -> RunStats:
    latencies_ms: list[float] = []
    success = 0

    sem = asyncio.Semaphore(concurrency)

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=timeout) as client:

        async def one_request() -> bool:
            nonlocal success
            async with sem:
                t0 = time.perf_counter()
                try:
                    resp = await client.get(f"{base_url}{endpoint}", headers=headers)
                    latencies_ms.append((time.perf_counter() - t0) * 1000.0)
                    if resp.status_code == 200:
                        success += 1
                        return True
                    return False
                except Exception:
                    latencies_ms.append((time.perf_counter() - t0) * 1000.0)
                    return False

        results = await asyncio.gather(*(one_request() for _ in range(total_requests)))

    total = len(results)
    failures = total - success
    avg_ms = statistics.mean(latencies_ms) if latencies_ms else 0.0
    return RunStats(
        total=total,
        success=success,
        failures=failures,
        p50_ms=percentile(latencies_ms, 0.50),
        p95_ms=percentile(latencies_ms, 0.95),
        p99_ms=percentile(latencies_ms, 0.99),
        avg_ms=avg_ms,
    )


def print_stats(label: str, stats: RunStats) -> None:
    success_rate = (stats.success / stats.total * 100.0) if stats.total else 0.0
    print(f"[{label}] total={stats.total} success={stats.success} failures={stats.failures} success_rate={success_rate:.2f}%")
    print(
        f"[{label}] latency_ms p50={stats.p50_ms:.2f} p95={stats.p95_ms:.2f} "
        f"p99={stats.p99_ms:.2f} avg={stats.avg_ms:.2f}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Concurrent load validation for OBELISK backend")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--total-requests", type=int, default=500)
    parser.add_argument("--concurrency", type=int, default=100)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--username", default=os.getenv("AUTH_USERNAME", "admin"))
    parser.add_argument("--password", default=os.getenv("AUTH_PASSWORD", "change_me"))
    parser.add_argument("--enforce", action="store_true", help="Fail with non-zero exit if SLOs are not met")
    parser.add_argument("--max-p95-ms", type=float, default=1000.0)
    parser.add_argument("--min-success-rate", type=float, default=99.0)
    return parser.parse_args()


async def main() -> int:
    args = parse_args()

    # Public endpoint load test
    public_stats = await run_load(
        args.base_url,
        "/health",
        total_requests=args.total_requests,
        concurrency=args.concurrency,
        token=None,
        timeout=args.timeout,
    )
    print_stats("health", public_stats)

    # Protected endpoint load test (auth + route dependencies)
    async with httpx.AsyncClient(timeout=args.timeout) as client:
        token = await login(client, args.base_url, args.username, args.password)

    protected_stats = await run_load(
        args.base_url,
        "/api/crawler/status",
        total_requests=args.total_requests,
        concurrency=args.concurrency,
        token=token,
        timeout=args.timeout,
    )
    print_stats("crawler_status", protected_stats)

    if not args.enforce:
        return 0

    # Gate on the protected endpoint to ensure authenticated path quality.
    success_rate = (protected_stats.success / protected_stats.total * 100.0) if protected_stats.total else 0.0
    if success_rate < args.min_success_rate:
        print(f"FAIL: success_rate {success_rate:.2f}% < {args.min_success_rate:.2f}%")
        return 2
    if protected_stats.p95_ms > args.max_p95_ms:
        print(f"FAIL: p95 {protected_stats.p95_ms:.2f}ms > {args.max_p95_ms:.2f}ms")
        return 3

    print("PASS: load-validation SLOs satisfied")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
