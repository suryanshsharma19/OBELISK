#!/usr/bin/env python3
"""OBELISK CI scanner for dependency and source-change risk gating.

This tool supports two scan paths:
1) dependency scan from manifests/lockfiles
2) code-change scan from git diff ranges (PR/push)

Each scan target is submitted to OBELISK's `/api/packages/analyze` endpoint
and evaluated against policy thresholds.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.11+ in CI
    tomllib = None  # type: ignore[assignment]

NPM_SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
PYPI_VERSION_PATTERN = re.compile(r"^[A-Za-z0-9]+(?:[A-Za-z0-9._+!-]*[A-Za-z0-9])?$")
REQUIREMENT_LINE_PATTERN = re.compile(
    r"^\s*([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?\s*([=!~<>]{1,3})?\s*([^;\s]+)?"
)

DEFAULT_IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
    ".tox",
}

DEFAULT_CODE_EXTENSIONS = (
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
)

ZERO_SHA = "0" * 40


@dataclass(frozen=True)
class Dependency:
    registry: str
    name: str
    version: str
    source_file: str
    dev_dependency: bool = False


@dataclass(frozen=True)
class ResolutionIssue:
    source_file: str
    dependency: str
    reason: str


@dataclass(frozen=True)
class ScanResult:
    dependency: Dependency
    risk_score: float | None
    threat_level: str | None
    is_blocked: bool
    blocked_reasons: list[str]
    package_id: int | None
    error: str | None = None
    blocked_alerts_marked: int = 0


@dataclass(frozen=True)
class CodeFileTarget:
    path: str
    registry: str
    name: str
    version: str
    bytes_size: int


@dataclass(frozen=True)
class CodeScanResult:
    target: CodeFileTarget
    risk_score: float | None
    threat_level: str | None
    is_blocked: bool
    blocked_reasons: list[str]
    package_id: int | None
    error: str | None = None
    blocked_alerts_marked: int = 0


class ObeliskApiError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class ObeliskClient:
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        timeout_seconds: float,
        retries: int,
        retry_backoff_seconds: float,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout_seconds = timeout_seconds
        self.retries = max(0, retries)
        self.retry_backoff_seconds = max(0.0, retry_backoff_seconds)
        self.token: str | None = None

    def login(self) -> None:
        payload = {"username": self.username, "password": self.password}
        data = self._request("POST", "/api/auth/login", payload=payload, include_auth=False)
        token = str(data.get("access_token", "")).strip()
        if not token:
            raise ObeliskApiError("Login succeeded but no access_token was returned")
        self.token = token

    def analyze_dependency(self, dependency: Dependency) -> dict[str, Any]:
        payload = {
            "name": dependency.name,
            "version": dependency.version,
            "registry": dependency.registry,
        }
        return self._request("POST", "/api/packages/analyze", payload=payload, include_auth=True)

    def analyze_code_change(self, target: CodeFileTarget, code: str) -> dict[str, Any]:
        payload = {
            "name": target.name,
            "version": target.version,
            "registry": target.registry,
            "code": code,
        }
        return self._request("POST", "/api/packages/analyze", payload=payload, include_auth=True)

    def mark_blocked_in_ci(self, package_id: int) -> int:
        package_detail = self._request(
            "GET",
            f"/api/packages/{package_id}",
            include_auth=True,
        )
        alerts = package_detail.get("alerts", [])
        if not isinstance(alerts, list):
            return 0

        marked = 0
        for alert in alerts:
            if not isinstance(alert, dict):
                continue
            alert_id = alert.get("id")
            if not isinstance(alert_id, int):
                continue
            self._request(
                "PUT",
                f"/api/alerts/{alert_id}?blocked_in_ci=true",
                include_auth=True,
            )
            marked += 1
        return marked

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        include_auth: bool = True,
    ) -> dict[str, Any]:
        url = urllib.parse.urljoin(f"{self.base_url}/", path.lstrip("/"))

        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if include_auth:
            if not self.token:
                raise ObeliskApiError("No authentication token available")
            headers["Authorization"] = f"Bearer {self.token}"

        request_data = None
        if payload is not None:
            request_data = json.dumps(payload).encode("utf-8")

        for attempt in range(self.retries + 1):
            request = urllib.request.Request(
                url=url,
                method=method,
                data=request_data,
                headers=headers,
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    raw = response.read().decode("utf-8")
                    if not raw:
                        return {}
                    data = json.loads(raw)
                    if isinstance(data, dict):
                        return data
                    raise ObeliskApiError(f"Unexpected JSON payload type from {path}")
            except urllib.error.HTTPError as exc:
                message = _extract_http_error_message(exc)
                if exc.code in {429, 500, 502, 503, 504} and attempt < self.retries:
                    time.sleep(self.retry_backoff_seconds * (2**attempt))
                    continue
                raise ObeliskApiError(
                    f"HTTP {exc.code} during {method} {path}: {message}",
                    status_code=exc.code,
                ) from exc
            except urllib.error.URLError as exc:
                if attempt < self.retries:
                    time.sleep(self.retry_backoff_seconds * (2**attempt))
                    continue
                raise ObeliskApiError(f"Network error during {method} {path}: {exc}") from exc
            except json.JSONDecodeError as exc:
                raise ObeliskApiError(f"Invalid JSON response for {method} {path}") from exc

        raise ObeliskApiError(f"Request failed after retries for {method} {path}")


def _extract_http_error_message(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8")
    except Exception:
        return str(exc)

    if not body:
        return str(exc)

    try:
        payload = json.loads(body)
        if isinstance(payload, dict):
            detail = payload.get("detail")
            if detail:
                return str(detail)
    except json.JSONDecodeError:
        pass

    return body


def discover_dependencies(repo_path: Path, include_dev: bool) -> tuple[list[Dependency], list[ResolutionIssue]]:
    manifests = discover_manifest_files(repo_path)

    dependencies: list[Dependency] = []
    issues: list[ResolutionIssue] = []

    for manifest in manifests:
        rel = manifest.relative_to(repo_path).as_posix()
        name = manifest.name

        try:
            if name in {"package-lock.json", "npm-shrinkwrap.json"}:
                deps, parse_issues = parse_package_lock(manifest, rel, include_dev)
            elif name == "package.json":
                deps, parse_issues = parse_package_json(manifest, rel, include_dev)
            elif name == "Pipfile.lock":
                deps, parse_issues = parse_pipfile_lock(manifest, rel, include_dev)
            elif name == "poetry.lock":
                deps, parse_issues = parse_poetry_lock(manifest, rel, include_dev)
            elif name.startswith("requirements") and name.endswith(".txt"):
                deps, parse_issues = parse_requirements_txt(manifest, rel)
            else:
                deps, parse_issues = [], []
        except Exception as exc:  # pragma: no cover - defensive guard
            deps, parse_issues = [], [
                ResolutionIssue(
                    source_file=rel,
                    dependency="*",
                    reason=f"Failed to parse manifest: {exc}",
                )
            ]

        dependencies.extend(deps)
        issues.extend(parse_issues)

    unique: dict[tuple[str, str, str], Dependency] = {}
    for dependency in dependencies:
        key = (dependency.registry, dependency.name.lower(), dependency.version)
        if key not in unique:
            unique[key] = dependency

    return sorted(unique.values(), key=lambda item: (item.registry, item.name.lower(), item.version)), issues


def discover_manifest_files(repo_path: Path) -> list[Path]:
    manifests: list[Path] = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [
            d
            for d in dirs
            if d not in DEFAULT_IGNORED_DIRS and not d.startswith(".venv")
        ]

        for filename in files:
            if filename in {
                "package-lock.json",
                "npm-shrinkwrap.json",
                "package.json",
                "Pipfile.lock",
                "poetry.lock",
            }:
                manifests.append(Path(root) / filename)
                continue

            if filename.startswith("requirements") and filename.endswith(".txt"):
                manifests.append(Path(root) / filename)

    return sorted(manifests)


def parse_package_lock(
    file_path: Path,
    rel_path: str,
    include_dev: bool,
) -> tuple[list[Dependency], list[ResolutionIssue]]:
    data = json.loads(file_path.read_text(encoding="utf-8"))
    dependencies: list[Dependency] = []
    issues: list[ResolutionIssue] = []

    packages = data.get("packages")
    if isinstance(packages, dict):
        for key, node in packages.items():
            if not key or "node_modules/" not in key or not isinstance(node, dict):
                continue

            package_name = key.split("node_modules/")[-1].strip()
            if not package_name:
                continue

            is_dev = bool(node.get("dev", False))
            if is_dev and not include_dev:
                continue

            raw_version = str(node.get("version", "")).strip()
            version = normalize_npm_version(raw_version)
            if not version:
                issues.append(
                    ResolutionIssue(
                        source_file=rel_path,
                        dependency=package_name,
                        reason=f"Unresolved npm version '{raw_version or '<missing>'}' in lockfile",
                    )
                )
                continue

            dependencies.append(
                Dependency(
                    registry="npm",
                    name=package_name,
                    version=version,
                    source_file=rel_path,
                    dev_dependency=is_dev,
                )
            )

        if dependencies:
            return dependencies, issues

    tree = data.get("dependencies")
    if isinstance(tree, dict):
        _walk_npm_dependency_tree(tree, rel_path, include_dev, dependencies, issues)

    return dependencies, issues


def _walk_npm_dependency_tree(
    tree: dict[str, Any],
    rel_path: str,
    include_dev: bool,
    dependencies: list[Dependency],
    issues: list[ResolutionIssue],
) -> None:
    for package_name, node in tree.items():
        if not isinstance(node, dict):
            continue

        is_dev = bool(node.get("dev", False))
        if is_dev and not include_dev:
            continue

        raw_version = str(node.get("version", "")).strip()
        version = normalize_npm_version(raw_version)
        if version:
            dependencies.append(
                Dependency(
                    registry="npm",
                    name=package_name,
                    version=version,
                    source_file=rel_path,
                    dev_dependency=is_dev,
                )
            )
        else:
            issues.append(
                ResolutionIssue(
                    source_file=rel_path,
                    dependency=package_name,
                    reason=f"Unresolved npm version '{raw_version or '<missing>'}' in lockfile tree",
                )
            )

        nested = node.get("dependencies")
        if isinstance(nested, dict):
            _walk_npm_dependency_tree(nested, rel_path, include_dev, dependencies, issues)


def parse_package_json(
    file_path: Path,
    rel_path: str,
    include_dev: bool,
) -> tuple[list[Dependency], list[ResolutionIssue]]:
    data = json.loads(file_path.read_text(encoding="utf-8"))
    dependencies: list[Dependency] = []
    issues: list[ResolutionIssue] = []

    sections = ["dependencies"]
    if include_dev:
        sections.append("devDependencies")

    for section in sections:
        values = data.get(section)
        if not isinstance(values, dict):
            continue

        for package_name, raw_spec in values.items():
            spec = str(raw_spec or "").strip()
            version = normalize_npm_version(spec)
            if not version:
                issues.append(
                    ResolutionIssue(
                        source_file=rel_path,
                        dependency=package_name,
                        reason=(
                            f"package.json spec '{spec or '<missing>'}' is not an exact version; "
                            "prefer package-lock.json for CI scanning"
                        ),
                    )
                )
                continue

            dependencies.append(
                Dependency(
                    registry="npm",
                    name=package_name,
                    version=version,
                    source_file=rel_path,
                    dev_dependency=section == "devDependencies",
                )
            )

    return dependencies, issues


def normalize_npm_version(raw_version: str) -> str | None:
    version = raw_version.strip()
    if version.startswith("v"):
        version = version[1:]
    if NPM_SEMVER_PATTERN.fullmatch(version):
        return version
    return None


def parse_requirements_txt(
    file_path: Path,
    rel_path: str,
) -> tuple[list[Dependency], list[ResolutionIssue]]:
    dependencies: list[Dependency] = []
    issues: list[ResolutionIssue] = []

    for line_number, raw in enumerate(file_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = _strip_inline_comment(raw)
        if not line:
            continue

        lowered = line.lower()
        if lowered.startswith(("-r", "--requirement", "-c", "--constraint", "--index-url", "--extra-index-url", "--find-links", "-f", "--trusted-host")):
            continue

        if lowered.startswith(("-e", "--editable", "git+", "http://", "https://", "file://")):
            issues.append(
                ResolutionIssue(
                    source_file=rel_path,
                    dependency=f"line:{line_number}",
                    reason="Editable/url requirement cannot be resolved to an exact package version",
                )
            )
            continue

        match = REQUIREMENT_LINE_PATTERN.match(line)
        if not match:
            issues.append(
                ResolutionIssue(
                    source_file=rel_path,
                    dependency=f"line:{line_number}",
                    reason=f"Unrecognized requirement format: {line}",
                )
            )
            continue

        package_name, operator, raw_version = match.groups()
        operator = operator or ""
        version = (raw_version or "").strip()

        if operator in {"==", "==="} and is_valid_pypi_version(version):
            dependencies.append(
                Dependency(
                    registry="pypi",
                    name=package_name,
                    version=version,
                    source_file=rel_path,
                )
            )
            continue

        issues.append(
            ResolutionIssue(
                source_file=rel_path,
                dependency=package_name,
                reason=(
                    f"Requirement '{line}' is not pinned with an exact version. "
                    "Use == or provide a lockfile for deterministic CI scans"
                ),
            )
        )

    return dependencies, issues


def _strip_inline_comment(line: str) -> str:
    line = line.strip()
    if not line or line.startswith("#"):
        return ""
    if " #" in line:
        line = line.split(" #", 1)[0].strip()
    return line


def parse_pipfile_lock(
    file_path: Path,
    rel_path: str,
    include_dev: bool,
) -> tuple[list[Dependency], list[ResolutionIssue]]:
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    dependencies: list[Dependency] = []
    issues: list[ResolutionIssue] = []

    sections = ["default"]
    if include_dev:
        sections.append("develop")

    for section in sections:
        values = payload.get(section)
        if not isinstance(values, dict):
            continue

        for package_name, meta in values.items():
            version_spec = ""
            if isinstance(meta, dict):
                version_spec = str(meta.get("version", "")).strip()
            elif isinstance(meta, str):
                version_spec = meta.strip()

            exact_version = ""
            if version_spec.startswith("==="):
                exact_version = version_spec[3:]
            elif version_spec.startswith("=="):
                exact_version = version_spec[2:]

            if exact_version and is_valid_pypi_version(exact_version):
                dependencies.append(
                    Dependency(
                        registry="pypi",
                        name=package_name,
                        version=exact_version,
                        source_file=rel_path,
                        dev_dependency=section == "develop",
                    )
                )
                continue

            issues.append(
                ResolutionIssue(
                    source_file=rel_path,
                    dependency=package_name,
                    reason=(
                        f"Pipfile.lock entry '{version_spec or '<missing>'}' is not an exact version"
                    ),
                )
            )

    return dependencies, issues


def parse_poetry_lock(
    file_path: Path,
    rel_path: str,
    include_dev: bool,
) -> tuple[list[Dependency], list[ResolutionIssue]]:
    if tomllib is None:
        return [], [
            ResolutionIssue(
                source_file=rel_path,
                dependency="*",
                reason="tomllib is unavailable; poetry.lock parsing requires Python 3.11+",
            )
        ]

    payload = tomllib.loads(file_path.read_text(encoding="utf-8"))
    packages = payload.get("package", [])
    dependencies: list[Dependency] = []
    issues: list[ResolutionIssue] = []

    if not isinstance(packages, list):
        return dependencies, issues

    for package_meta in packages:
        if not isinstance(package_meta, dict):
            continue

        category = str(package_meta.get("category", "main"))
        groups = package_meta.get("groups", [])
        is_dev = category != "main"
        if isinstance(groups, list) and "main" not in groups:
            is_dev = True

        if is_dev and not include_dev:
            continue

        package_name = str(package_meta.get("name", "")).strip()
        version = str(package_meta.get("version", "")).strip()

        if not package_name:
            continue

        if not is_valid_pypi_version(version):
            issues.append(
                ResolutionIssue(
                    source_file=rel_path,
                    dependency=package_name,
                    reason=f"poetry.lock version '{version or '<missing>'}' is not valid",
                )
            )
            continue

        dependencies.append(
            Dependency(
                registry="pypi",
                name=package_name,
                version=version,
                source_file=rel_path,
                dev_dependency=is_dev,
            )
        )

    return dependencies, issues


def is_valid_pypi_version(version: str) -> bool:
    return bool(version and PYPI_VERSION_PATTERN.fullmatch(version))


def parse_allowed_extensions(raw: str) -> tuple[str, ...]:
    values: list[str] = []
    for item in raw.split(","):
        ext = item.strip().lower()
        if not ext:
            continue
        if not ext.startswith("."):
            ext = f".{ext}"
        values.append(ext)

    if not values:
        return DEFAULT_CODE_EXTENSIONS

    return tuple(dict.fromkeys(values))


def determine_registry_for_path(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".py":
        return "pypi"
    return "npm"


def normalize_scan_package_name(path: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9._-]+", "-", path.strip().lower()).strip("-")
    if not base:
        base = "file"
    return f"repo-file-{base[:120]}"


def resolve_git_diff_range(repo_path: Path, explicit_range: str) -> str | None:
    if explicit_range.strip():
        return explicit_range.strip()

    event_name = os.getenv("GITHUB_EVENT_NAME", "").strip().lower()
    base_ref = os.getenv("GITHUB_BASE_REF", "").strip()
    before_sha = os.getenv("GITHUB_EVENT_BEFORE", "").strip() or os.getenv("GITHUB_BEFORE", "").strip()

    if event_name == "pull_request" and base_ref:
        return f"origin/{base_ref}...HEAD"

    if before_sha and before_sha != ZERO_SHA:
        return f"{before_sha}...HEAD"

    # Fallback for local runs and single-commit push contexts.
    if _git_ref_exists(repo_path, "HEAD~1"):
        return "HEAD~1...HEAD"

    return None


def _git_ref_exists(repo_path: Path, ref: str) -> bool:
    proc = subprocess.run(
        ["git", "-C", str(repo_path), "rev-parse", "--verify", "--quiet", ref],
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def _git_name_only_changed_files(repo_path: Path, diff_range: str) -> tuple[list[str], str | None]:
    proc = subprocess.run(
        [
            "git",
            "-C",
            str(repo_path),
            "diff",
            "--name-only",
            "--diff-filter=AMRC",
            diff_range,
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        stderr = (proc.stderr or proc.stdout or "git diff failed").strip()
        return [], stderr

    files = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return files, None


def discover_changed_code_targets(
    repo_path: Path,
    diff_range: str,
    allowed_extensions: tuple[str, ...],
    max_changed_files: int,
    max_code_file_bytes: int,
) -> tuple[list[CodeFileTarget], list[ResolutionIssue]]:
    changed_files, git_error = _git_name_only_changed_files(repo_path, diff_range)
    if git_error:
        return [], [
            ResolutionIssue(
                source_file="<git-diff>",
                dependency="*",
                reason=f"Unable to resolve changed files from git diff range '{diff_range}': {git_error}",
            )
        ]

    issues: list[ResolutionIssue] = []
    targets: list[CodeFileTarget] = []

    if len(changed_files) > max_changed_files:
        issues.append(
            ResolutionIssue(
                source_file="<git-diff>",
                dependency="*",
                reason=(
                    f"Changed file count {len(changed_files)} exceeds max_changed_files={max_changed_files}; "
                    "scan truncated"
                ),
            )
        )
        changed_files = changed_files[:max_changed_files]

    for rel_path in changed_files:
        suffix = Path(rel_path).suffix.lower()
        if suffix not in allowed_extensions:
            continue

        abs_path = repo_path / rel_path
        if not abs_path.exists() or not abs_path.is_file():
            issues.append(
                ResolutionIssue(
                    source_file=rel_path,
                    dependency="*",
                    reason="Changed file is not available in workspace (possibly removed/renamed)",
                )
            )
            continue

        file_size = abs_path.stat().st_size
        if file_size > max_code_file_bytes:
            issues.append(
                ResolutionIssue(
                    source_file=rel_path,
                    dependency="*",
                    reason=(
                        f"Changed code file size {file_size} exceeds max_code_file_bytes={max_code_file_bytes}; skipped"
                    ),
                )
            )
            continue

        targets.append(
            CodeFileTarget(
                path=rel_path,
                registry=determine_registry_for_path(rel_path),
                name=normalize_scan_package_name(rel_path),
                version="0.0.0",
                bytes_size=file_size,
            )
        )

    return targets, issues


def read_code_target(repo_path: Path, target: CodeFileTarget, max_code_chars: int) -> str:
    abs_path = repo_path / target.path
    data = abs_path.read_bytes()
    if b"\x00" in data:
        raise ValueError("Binary file detected")

    text = data.decode("utf-8", errors="replace")
    if len(text) > max_code_chars:
        text = text[:max_code_chars]

    return text


def parse_block_threat_levels(text: str) -> set[str]:
    levels = {item.strip().lower() for item in text.split(",") if item.strip()}
    if not levels:
        return {"high", "critical"}
    return levels


def evaluate_policy(
    risk_score: float,
    threat_level: str,
    risk_threshold: float,
    blocked_threat_levels: set[str],
) -> tuple[bool, list[str]]:
    blocked = False
    reasons: list[str] = []

    if threat_level.lower() in blocked_threat_levels:
        blocked = True
        reasons.append(f"threat_level={threat_level}")

    if risk_score >= risk_threshold:
        blocked = True
        reasons.append(f"risk_score={risk_score:.2f}>=threshold={risk_threshold:.2f}")

    return blocked, reasons


def run_scan(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    repo_path = Path(args.repo_path).resolve()
    if not repo_path.exists() or not repo_path.is_dir():
        raise SystemExit(f"Repository path does not exist or is not a directory: {repo_path}")

    dependencies, dependency_issues = discover_dependencies(
        repo_path,
        include_dev=args.include_dev_dependencies,
    )

    allowed_extensions = parse_allowed_extensions(args.allowed_code_extensions)
    diff_range_used: str | None = None
    code_targets: list[CodeFileTarget] = []
    code_issues: list[ResolutionIssue] = []

    if args.scan_changed_code:
        diff_range_used = resolve_git_diff_range(repo_path, args.git_diff_range)
        if not diff_range_used:
            code_issues.append(
                ResolutionIssue(
                    source_file="<git-diff>",
                    dependency="*",
                    reason="Unable to infer git diff range. Provide --git-diff-range explicitly.",
                )
            )
        else:
            code_targets, code_issues = discover_changed_code_targets(
                repo_path=repo_path,
                diff_range=diff_range_used,
                allowed_extensions=allowed_extensions,
                max_changed_files=args.max_changed_files,
                max_code_file_bytes=args.max_code_file_bytes,
            )

    blocked_levels = parse_block_threat_levels(args.block_threat_levels)
    all_issues = [*dependency_issues, *code_issues]

    report: dict[str, Any] = {
        "repo_path": str(repo_path),
        "dependencies_discovered": len(dependencies),
        "resolution_issues": [asdict(issue) for issue in all_issues],
        "blocked_threat_levels": sorted(blocked_levels),
        "risk_threshold": args.risk_threshold,
        "scan_results": [],
        "code_scan": {
            "enabled": bool(args.scan_changed_code),
            "diff_range": diff_range_used,
            "targets_discovered": len(code_targets),
            "issues": [asdict(issue) for issue in code_issues],
            "results": [],
        },
        "summary": {},
    }

    if dependency_issues and args.fail_on_unresolved:
        report["summary"] = {
            "status": "failed",
            "reason": "unresolved_dependencies",
            "blocked_count": 0,
            "error_count": 0,
            "scanned_count": 0,
        }
        return 3, report

    if args.scan_changed_code and args.fail_on_missing_diff_range and not diff_range_used:
        report["summary"] = {
            "status": "failed",
            "reason": "missing_diff_range",
            "blocked_count": 0,
            "error_count": 0,
            "scanned_count": 0,
        }
        return 4, report

    if not dependencies and not code_targets:
        report["summary"] = {
            "status": "passed",
            "blocked_count": 0,
            "error_count": 0,
            "scanned_count": 0,
        }
        return 0, report

    client = ObeliskClient(
        base_url=args.api_base_url,
        username=args.auth_username,
        password=args.auth_password,
        timeout_seconds=args.timeout_seconds,
        retries=args.retries,
        retry_backoff_seconds=args.retry_backoff_seconds,
    )

    client.login()

    scan_results: list[ScanResult] = []
    code_scan_results: list[CodeScanResult] = []

    for dependency in dependencies:
        time.sleep(args.request_delay_seconds)

        try:
            response = client.analyze_dependency(dependency)
            analysis = response.get("analysis", {}) if isinstance(response, dict) else {}
            package_payload = response.get("package", {}) if isinstance(response, dict) else {}

            risk_score = float(analysis.get("risk_score", 0.0) or 0.0)
            threat_level = str(analysis.get("threat_level", "safe") or "safe")
            package_id = package_payload.get("id") if isinstance(package_payload, dict) else None
            if not isinstance(package_id, int):
                package_id = None

            is_blocked, reasons = evaluate_policy(
                risk_score=risk_score,
                threat_level=threat_level,
                risk_threshold=args.risk_threshold,
                blocked_threat_levels=blocked_levels,
            )

            marked_alerts = 0
            if is_blocked and args.mark_blocked_in_ci and package_id is not None:
                marked_alerts = client.mark_blocked_in_ci(package_id)

            scan_results.append(
                ScanResult(
                    dependency=dependency,
                    risk_score=risk_score,
                    threat_level=threat_level,
                    is_blocked=is_blocked,
                    blocked_reasons=reasons,
                    package_id=package_id,
                    blocked_alerts_marked=marked_alerts,
                )
            )
        except Exception as exc:  # noqa: BLE001 - CI should capture and report all failures
            scan_results.append(
                ScanResult(
                    dependency=dependency,
                    risk_score=None,
                    threat_level=None,
                    is_blocked=False,
                    blocked_reasons=[],
                    package_id=None,
                    error=str(exc),
                )
            )
            if args.fail_on_scan_error:
                break

    if not (args.fail_on_scan_error and any(item.error for item in scan_results)):
        for target in code_targets:
            time.sleep(args.request_delay_seconds)

            try:
                code_text = read_code_target(repo_path, target, args.max_code_chars)
                response = client.analyze_code_change(target, code_text)
                analysis = response.get("analysis", {}) if isinstance(response, dict) else {}
                package_payload = response.get("package", {}) if isinstance(response, dict) else {}

                risk_score = float(analysis.get("risk_score", 0.0) or 0.0)
                threat_level = str(analysis.get("threat_level", "safe") or "safe")
                package_id = package_payload.get("id") if isinstance(package_payload, dict) else None
                if not isinstance(package_id, int):
                    package_id = None

                is_blocked, reasons = evaluate_policy(
                    risk_score=risk_score,
                    threat_level=threat_level,
                    risk_threshold=args.risk_threshold,
                    blocked_threat_levels=blocked_levels,
                )

                marked_alerts = 0
                if is_blocked and args.mark_blocked_in_ci and package_id is not None:
                    marked_alerts = client.mark_blocked_in_ci(package_id)

                code_scan_results.append(
                    CodeScanResult(
                        target=target,
                        risk_score=risk_score,
                        threat_level=threat_level,
                        is_blocked=is_blocked,
                        blocked_reasons=reasons,
                        package_id=package_id,
                        blocked_alerts_marked=marked_alerts,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                code_scan_results.append(
                    CodeScanResult(
                        target=target,
                        risk_score=None,
                        threat_level=None,
                        is_blocked=False,
                        blocked_reasons=[],
                        package_id=None,
                        error=str(exc),
                    )
                )
                if args.fail_on_scan_error:
                    break

    blocked_count = sum(1 for item in scan_results if item.is_blocked) + sum(
        1 for item in code_scan_results if item.is_blocked
    )
    error_count = sum(1 for item in scan_results if item.error) + sum(
        1 for item in code_scan_results if item.error
    )

    report["scan_results"] = [
        {
            "dependency": asdict(item.dependency),
            "risk_score": item.risk_score,
            "threat_level": item.threat_level,
            "is_blocked": item.is_blocked,
            "blocked_reasons": item.blocked_reasons,
            "package_id": item.package_id,
            "error": item.error,
            "blocked_alerts_marked": item.blocked_alerts_marked,
        }
        for item in scan_results
    ]
    report["code_scan"]["results"] = [
        {
            "target": asdict(item.target),
            "risk_score": item.risk_score,
            "threat_level": item.threat_level,
            "is_blocked": item.is_blocked,
            "blocked_reasons": item.blocked_reasons,
            "package_id": item.package_id,
            "error": item.error,
            "blocked_alerts_marked": item.blocked_alerts_marked,
        }
        for item in code_scan_results
    ]

    status = "passed"
    exit_code = 0

    if error_count:
        status = "failed"
        if args.fail_on_scan_error:
            exit_code = 2

    if blocked_count:
        status = "blocked"
        exit_code = 1

    report["summary"] = {
        "status": status,
        "blocked_count": blocked_count,
        "error_count": error_count,
        "dependency_scanned_count": len(scan_results),
        "code_scanned_count": len(code_scan_results),
        "scanned_count": len(scan_results) + len(code_scan_results),
    }

    return exit_code, report


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan repository dependencies with OBELISK and enforce CI policy",
    )
    parser.add_argument("--repo-path", default=".", help="Path to the target repository to scan")
    parser.add_argument("--api-base-url", required=True, help="OBELISK backend base URL")
    parser.add_argument("--auth-username", required=True, help="OBELISK API username")
    parser.add_argument("--auth-password", required=True, help="OBELISK API password")

    parser.add_argument(
        "--risk-threshold",
        type=float,
        default=60.0,
        help="Block when risk_score is greater than or equal to this value",
    )
    parser.add_argument(
        "--block-threat-levels",
        default="high,critical",
        help="Comma-separated threat levels that should hard block",
    )
    parser.add_argument(
        "--include-dev-dependencies",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include dev/test dependencies when scanning manifests (default: enabled)",
    )
    parser.add_argument(
        "--scan-changed-code",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Analyze changed source files from git diff (default: enabled)",
    )
    parser.add_argument(
        "--git-diff-range",
        default="",
        help="Explicit git diff range for code scan (for example base_sha...head_sha)",
    )
    parser.add_argument(
        "--fail-on-missing-diff-range",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Fail if code scan is enabled but no diff range can be inferred",
    )
    parser.add_argument(
        "--allowed-code-extensions",
        default=",".join(DEFAULT_CODE_EXTENSIONS),
        help="Comma-separated file extensions for changed code scanning",
    )
    parser.add_argument(
        "--max-changed-files",
        type=int,
        default=300,
        help="Maximum changed files to inspect in code scan",
    )
    parser.add_argument(
        "--max-code-file-bytes",
        type=int,
        default=200_000,
        help="Maximum per-file byte size for code scan targets",
    )
    parser.add_argument(
        "--max-code-chars",
        type=int,
        default=30_000,
        help="Maximum code characters submitted per changed file",
    )
    parser.add_argument(
        "--fail-on-unresolved",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Fail when manifests contain unresolved (non-exact) versions",
    )
    parser.add_argument(
        "--fail-on-scan-error",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Fail if analyze API calls return errors",
    )
    parser.add_argument(
        "--mark-blocked-in-ci",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Mark related alert entries as blocked_in_ci=true when possible",
    )

    parser.add_argument("--timeout-seconds", type=float, default=30.0, help="HTTP request timeout")
    parser.add_argument("--retries", type=int, default=2, help="Retry count for transient API failures")
    parser.add_argument(
        "--retry-backoff-seconds",
        type=float,
        default=0.6,
        help="Initial retry backoff; each retry doubles this delay",
    )
    parser.add_argument(
        "--request-delay-seconds",
        type=float,
        default=0.0,
        help="Optional fixed delay inserted between API analyze requests",
    )

    parser.add_argument(
        "--output-json",
        default="",
        help="Optional file path to write full scan report JSON",
    )

    return parser


def print_human_summary(report: dict[str, Any]) -> None:
    summary = report.get("summary", {})
    code_scan = report.get("code_scan", {})
    print("OBELISK CI Dependency Scan")
    print("==========================")
    print(f"Repo:          {report.get('repo_path')}")
    print(f"Discovered:    {report.get('dependencies_discovered', 0)} dependencies")
    print(f"Code Targets:  {code_scan.get('targets_discovered', 0)}")
    if code_scan.get("enabled"):
        print(f"Diff Range:    {code_scan.get('diff_range') or '<unresolved>'}")
    print(f"Scanned:       {summary.get('scanned_count', 0)}")
    print(f"Blocked:       {summary.get('blocked_count', 0)}")
    print(f"Errors:        {summary.get('error_count', 0)}")
    print(f"Status:        {summary.get('status', 'unknown')}")

    issues = report.get("resolution_issues", [])
    if issues:
        print("\nResolution issues:")
        for issue in issues[:15]:
            print(
                f"- {issue.get('source_file')}: {issue.get('dependency')} -> {issue.get('reason')}"
            )
        if len(issues) > 15:
            print(f"- ... and {len(issues) - 15} more")

    blocked = [item for item in report.get("scan_results", []) if item.get("is_blocked")]
    if blocked:
        print("\nBlocked dependencies:")
        for entry in blocked:
            dep = entry.get("dependency", {})
            reasons = ", ".join(entry.get("blocked_reasons", []))
            print(
                f"- {dep.get('registry')}:{dep.get('name')}@{dep.get('version')} "
                f"(risk={entry.get('risk_score')}, threat={entry.get('threat_level')}) [{reasons}]"
            )

    blocked_code = [
        item for item in code_scan.get("results", []) if isinstance(item, dict) and item.get("is_blocked")
    ]
    if blocked_code:
        print("\nBlocked changed files:")
        for entry in blocked_code:
            target = entry.get("target", {})
            reasons = ", ".join(entry.get("blocked_reasons", []))
            print(
                f"- {target.get('path')} "
                f"(risk={entry.get('risk_score')}, threat={entry.get('threat_level')}) [{reasons}]"
            )

    errors = [item for item in report.get("scan_results", []) if item.get("error")]
    if errors:
        print("\nScan errors:")
        for entry in errors[:15]:
            dep = entry.get("dependency", {})
            print(
                f"- {dep.get('registry')}:{dep.get('name')}@{dep.get('version')} -> {entry.get('error')}"
            )
        if len(errors) > 15:
            print(f"- ... and {len(errors) - 15} more")

    code_errors = [
        item for item in code_scan.get("results", []) if isinstance(item, dict) and item.get("error")
    ]
    if code_errors:
        print("\nCode scan errors:")
        for entry in code_errors[:15]:
            target = entry.get("target", {})
            print(f"- {target.get('path')} -> {entry.get('error')}")
        if len(code_errors) > 15:
            print(f"- ... and {len(code_errors) - 15} more")


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    try:
        exit_code, report = run_scan(args)
    except Exception as exc:  # noqa: BLE001
        print(f"Fatal scanner error: {exc}", file=sys.stderr)
        return 2

    print_human_summary(report)

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"\nWrote report JSON: {output_path}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
