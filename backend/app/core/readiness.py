"""Startup and runtime readiness checks for production safety gates."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import text

from app.config import Settings, get_settings
from app.core.logging import setup_logger

logger = setup_logger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _backend_root() -> Path:
    # backend/app/core/readiness.py -> backend/
    return Path(__file__).resolve().parents[2]


def _resolve_model_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return _backend_root() / path


def _run_named_check(name: str, func: Callable[[], Any]) -> dict[str, Any]:
    try:
        func()
        return {
            "ok": True,
            "status": "ready",
            "detail": f"{name} reachable",
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": "degraded",
            "detail": str(exc),
        }


def _is_placeholder_secret(value: str) -> bool:
    placeholders = {
        "",
        "CHANGE_ME_SECRET_KEY_64PLUS_CHARS",
        "CHANGE_ME_AUTH_PASSWORD",
        "change_me",
        "replace_me",
    }
    return value in placeholders


def _contains_localhost_origin(origins: list[str]) -> bool:
    prefixes = (
        "http://localhost",
        "http://127.0.0.1",
        "https://localhost",
        "https://127.0.0.1",
    )
    return any(origin.startswith(prefixes) for origin in origins)


def check_security_baseline(settings: Settings) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    failures: list[str] = []

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

    if settings.environment == "local":
        return {
            "ok": True,
            "status": "skipped",
            "checked_at": _utc_now_iso(),
            "checks": {
                "environment": {
                    "ok": True,
                    "status": "skipped",
                    "detail": "Local environment: strict security baseline skipped",
                },
            },
            "failures": [],
        }

    # Non-local environments should enforce explicit, non-default secrets.
    secret_key_ok = not _is_placeholder_secret(settings.secret_key) and len(settings.secret_key) >= 32
    checks["secret_key"] = {
        "ok": secret_key_ok,
        "status": "ready" if secret_key_ok else "degraded",
        "detail": "secret key is strong" if secret_key_ok else "secret key is default/weak",
    }
    if not secret_key_ok and settings.enforce_strong_secrets:
        failures.append("secret_key must be non-default and >= 32 chars")

    auth_password_ok = not _is_placeholder_secret(settings.auth_password) and len(settings.auth_password) >= 12
    checks["auth_password"] = {
        "ok": auth_password_ok,
        "status": "ready" if auth_password_ok else "degraded",
        "detail": "auth password is strong" if auth_password_ok else "auth password is default/weak",
    }
    if not auth_password_ok and settings.enforce_strong_secrets:
        failures.append("auth_password must be non-default and >= 12 chars")

    secure_cookie_ok = bool(settings.secure_cookies)
    checks["secure_cookies"] = {
        "ok": secure_cookie_ok,
        "status": "ready" if secure_cookie_ok else "degraded",
        "detail": "secure cookies enabled" if secure_cookie_ok else "secure cookies disabled",
    }
    if not secure_cookie_ok:
        failures.append("secure_cookies must be true in non-local environments")

    has_origins = len(origins) > 0
    localhost_allowed = settings.allow_localhost_cors_in_non_local
    localhost_present = _contains_localhost_origin(origins)
    cors_ok = has_origins and (localhost_allowed or not localhost_present)
    checks["cors_origins"] = {
        "ok": cors_ok,
        "status": "ready" if cors_ok else "degraded",
        "detail": (
            "CORS origins configured and non-local safe"
            if cors_ok
            else "CORS origins invalid for non-local runtime"
        ),
    }
    if not cors_ok:
        failures.append("cors_origins must not be empty and must exclude localhost in non-local environments")

    return {
        "ok": not failures,
        "status": "ready" if not failures else "degraded",
        "checked_at": _utc_now_iso(),
        "checks": checks,
        "failures": failures,
    }


def check_model_artifacts(settings: Settings) -> dict[str, Any]:
    required_files = {
        "codebert_config": _resolve_model_path(settings.codebert_model_path) / "config.json",
        "gnn_model": _resolve_model_path(settings.gnn_model_path) / "model.pt",
        "isolation_forest_model": _resolve_model_path(settings.isolation_forest_path) / "model.joblib",
    }

    checks: dict[str, Any] = {}
    failures: list[str] = []

    for check_name, path in required_files.items():
        exists = path.exists()
        checks[check_name] = {
            "ok": exists,
            "status": "ready" if exists else "degraded",
            "path": str(path),
            "detail": "artifact present" if exists else "artifact missing",
        }
        if not exists:
            failures.append(f"{check_name}: missing {path}")

    return {
        "ok": not failures,
        "status": "ready" if not failures else "degraded",
        "checked_at": _utc_now_iso(),
        "checks": checks,
        "failures": failures,
    }


def check_dependency_readiness() -> dict[str, Any]:
    def _check_postgres() -> None:
        from app.db.session import engine

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

    def _check_redis() -> None:
        from app.db.redis_client import redis_client

        if not redis_client.client.ping():
            raise RuntimeError("Redis ping returned false")

    def _check_neo4j() -> None:
        from app.db.neo4j_client import neo4j_client

        result = neo4j_client.run_query("RETURN 1 AS ok")
        if not result:
            raise RuntimeError("Neo4j returned no rows")

    checks = {
        "postgres": _run_named_check("PostgreSQL", _check_postgres),
        "redis": _run_named_check("Redis", _check_redis),
        "neo4j": _run_named_check("Neo4j", _check_neo4j),
    }

    failures = [
        f"{name}: {entry['detail']}"
        for name, entry in checks.items()
        if not entry["ok"]
    ]

    return {
        "ok": not failures,
        "status": "ready" if not failures else "degraded",
        "checked_at": _utc_now_iso(),
        "checks": checks,
        "failures": failures,
    }


def collect_runtime_readiness(include_dependencies: bool = True) -> dict[str, Any]:
    settings = get_settings()

    model_report = check_model_artifacts(settings)
    security_report = check_security_baseline(settings)
    if include_dependencies:
        dependency_report = check_dependency_readiness()
    else:
        dependency_report = {
            "ok": True,
            "status": "skipped",
            "checked_at": _utc_now_iso(),
            "checks": {},
            "failures": [],
        }

    ready = model_report["ok"] and dependency_report["ok"] and security_report["ok"]
    failures = [
        *[f"model::{entry}" for entry in model_report["failures"]],
        *[f"dependency::{entry}" for entry in dependency_report["failures"]],
        *[f"security::{entry}" for entry in security_report["failures"]],
    ]

    return {
        "status": "ready" if ready else "degraded",
        "ready": ready,
        "checked_at": _utc_now_iso(),
        "checks": {
            "model_artifacts": model_report,
            "dependencies": dependency_report,
            "security_baseline": security_report,
        },
        "failures": failures,
    }


def run_startup_readiness_or_raise(
    *,
    strict: bool,
    include_dependencies: bool,
) -> dict[str, Any]:
    report = collect_runtime_readiness(include_dependencies=include_dependencies)

    if report["ready"]:
        logger.info("Startup readiness checks passed")
    else:
        logger.warning("Startup readiness is degraded: %s", report["failures"])

    if strict and not report["ready"]:
        raise RuntimeError(
            "Startup readiness checks failed: " + "; ".join(report["failures"]),
        )

    return report