"""Fetches and normalises package metadata from npm and PyPI."""

from __future__ import annotations

import io
import tarfile
from typing import Any
import zipfile

import httpx

from app.config import get_settings
from app.core.exceptions import RegistryError
from app.core.logging import setup_logger

logger = setup_logger(__name__)
settings = get_settings()

# http timeout (seconds)
REQUEST_TIMEOUT = 15.0

MAX_FILE_BYTES = 200_000
SKIP_PATH_SEGMENTS = ("node_modules/", ".git/", "__pycache__/", "dist/", "build/")
ALLOWED_SOURCE_SUFFIXES = (
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".py", ".json", ".toml", ".yaml", ".yml", ".ini", ".cfg", ".sh",
)


async def fetch_package_metadata(
    name: str,
    version: str,
    registry: str,
) -> dict[str, Any]:
    if registry == "npm":
        return await fetch_npm_metadata(name, version)
    elif registry == "pypi":
        return await fetch_pypi_metadata(name, version)
    else:
        raise RegistryError(f"Unsupported registry: {registry}")


async def fetch_npm_metadata(name: str, version: str) -> dict[str, Any]:
    base = settings.npm_registry_url.rstrip("/")

    root_url = f"{base}/{name}"
    root_data = await _http_get(root_url)

    raw: dict[str, Any] | None = None
    published_at = ""

    if root_data:
        versions = root_data.get("versions", {})
        if version in versions:
            raw = versions.get(version)
        else:
            latest = root_data.get("dist-tags", {}).get("latest")
            raw = versions.get(latest, {}) if latest else {}

        selected_version = str((raw or {}).get("version") or version)
        published_at = _extract_npm_published_at(root_data, selected_version)

    if not raw:
        # fallback to version-specific endpoint
        raw = await _http_get(f"{base}/{name}/{version}")

    if raw is None:
        logger.warning("npm lookup failed for %s@%s", name, version)
        return {
            "name": name,
            "version": version,
            "weekly_downloads": 0,
            "published_at": "",
        }

    weekly_downloads = await _fetch_npm_weekly_downloads(name)
    return _normalise_npm(raw, name, version, weekly_downloads, published_at)


def _normalise_npm(
    raw: dict[str, Any],
    name: str,
    version: str,
    weekly_downloads: int,
    published_at: str,
) -> dict[str, Any]:
    return {
        "name": raw.get("name", name),
        "version": raw.get("version", version),
        "description": raw.get("description", ""),
        "author": raw.get("author", {}),
        "license": raw.get("license", ""),
        "repository": raw.get("repository", {}),
        "dependencies": raw.get("dependencies", {}),
        "devDependencies": raw.get("devDependencies", {}),
        "scripts": raw.get("scripts", {}),
        "maintainers": raw.get("maintainers", []),
        "maintainer": _first_maintainer(raw.get("maintainers", [])),
        "keywords": raw.get("keywords", []),
        "homepage": raw.get("homepage", ""),
        "dist": raw.get("dist", {}),
        "weekly_downloads": max(weekly_downloads, 0),
        "published_at": published_at,
    }


async def fetch_pypi_metadata(name: str, version: str) -> dict[str, Any]:
    base = settings.pypi_registry_url.rstrip("/")

    version_data = await _http_get(f"{base}/{name}/{version}/json")
    root_data = version_data
    if root_data is None:
        root_data = await _http_get(f"{base}/{name}/json")

    if root_data is None:
        logger.warning("PyPI lookup failed for %s@%s", name, version)
        return {
            "name": name,
            "version": version,
            "weekly_downloads": 0,
            "published_at": "",
        }

    weekly_downloads = await _fetch_pypi_weekly_downloads(name)
    published_at = _extract_pypi_published_at(root_data, version)

    return _normalise_pypi(root_data, name, version, weekly_downloads, published_at)


def _normalise_pypi(
    raw: dict[str, Any],
    name: str,
    version: str,
    weekly_downloads: int,
    published_at: str,
) -> dict[str, Any]:
    info = raw.get("info", {})
    urls = raw.get("urls", [])

    dependencies = {
        dep: ""
        for dep in info.get("requires_dist", [])
        if isinstance(dep, str)
    }

    return {
        "name": info.get("name", name),
        "version": info.get("version", version),
        "description": info.get("summary", ""),
        "author": {"name": info.get("author", ""), "email": info.get("author_email", "")},
        "license": info.get("license", ""),
        "repository": {"url": info.get("project_urls", {}).get("Source", "")},
        "dependencies": dependencies,
        "scripts": {},
        "maintainer": {
            "email": info.get("maintainer_email", info.get("author_email", "")),
        },
        "keywords": info.get("keywords", "").split(",") if info.get("keywords") else [],
        "homepage": info.get("home_page", ""),
        "urls": urls,
        "weekly_downloads": max(weekly_downloads, 0),
        "published_at": published_at,
    }


async def fetch_package_source_code(
    name: str,
    version: str,
    registry: str,
    metadata: dict[str, Any],
) -> str:
    archive_url = _resolve_archive_url(registry, metadata)
    if not archive_url:
        return ""

    blob = await _http_get_bytes(archive_url)
    if not blob:
        return ""

    code = _extract_source_from_archive(blob, archive_url)
    if code:
        logger.info(
            "Fetched package source for %s@%s (%s), chars=%d",
            name,
            version,
            registry,
            len(code),
        )
    return code


def _resolve_archive_url(registry: str, metadata: dict[str, Any]) -> str:
    if registry == "npm":
        return str(metadata.get("dist", {}).get("tarball", ""))

    if registry == "pypi":
        urls = metadata.get("urls", [])
        if isinstance(urls, list):
            for item in urls:
                if isinstance(item, dict) and item.get("packagetype") == "sdist" and item.get("url"):
                    return str(item["url"])
            for item in urls:
                if isinstance(item, dict) and item.get("url"):
                    return str(item["url"])

    return ""


def _extract_source_from_archive(blob: bytes, archive_url: str) -> str:
    lower_url = archive_url.lower()
    if lower_url.endswith((".tar.gz", ".tgz", ".tar")):
        return _extract_tar_source(blob)
    if lower_url.endswith(".zip"):
        return _extract_zip_source(blob)

    # Try both archive formats as a fallback.
    tar_code = _extract_tar_source(blob)
    if tar_code:
        return tar_code
    return _extract_zip_source(blob)


def _extract_tar_source(blob: bytes) -> str:
    snippets: list[str] = []
    chars = 0
    files = 0

    try:
        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:*") as archive:
            for member in archive.getmembers():
                if files >= settings.source_extract_max_files:
                    break
                if chars >= settings.source_extract_max_chars:
                    break
                if not member.isfile() or member.size <= 0 or member.size > MAX_FILE_BYTES:
                    continue
                if not _allow_source_path(member.name):
                    continue

                extracted = archive.extractfile(member)
                if extracted is None:
                    continue

                content = extracted.read(MAX_FILE_BYTES)
                text = content.decode("utf-8", errors="replace").strip()
                if not text:
                    continue

                chunk = _format_source_chunk(member.name, text)
                remaining = settings.source_extract_max_chars - chars
                if remaining <= 0:
                    break
                if len(chunk) > remaining:
                    chunk = chunk[:remaining]

                snippets.append(chunk)
                chars += len(chunk)
                files += 1
    except Exception as exc:
        logger.debug("tar extraction skipped: %s", exc)

    return "\n".join(snippets).strip()


def _extract_zip_source(blob: bytes) -> str:
    snippets: list[str] = []
    chars = 0
    files = 0

    try:
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            for member in archive.infolist():
                if files >= settings.source_extract_max_files:
                    break
                if chars >= settings.source_extract_max_chars:
                    break
                if member.is_dir() or member.file_size <= 0 or member.file_size > MAX_FILE_BYTES:
                    continue
                if not _allow_source_path(member.filename):
                    continue

                content = archive.read(member)
                text = content.decode("utf-8", errors="replace").strip()
                if not text:
                    continue

                chunk = _format_source_chunk(member.filename, text)
                remaining = settings.source_extract_max_chars - chars
                if remaining <= 0:
                    break
                if len(chunk) > remaining:
                    chunk = chunk[:remaining]

                snippets.append(chunk)
                chars += len(chunk)
                files += 1
    except Exception as exc:
        logger.debug("zip extraction skipped: %s", exc)

    return "\n".join(snippets).strip()


def _allow_source_path(path: str) -> bool:
    lowered = path.lower().strip("/")
    if not lowered:
        return False
    if any(segment in lowered for segment in SKIP_PATH_SEGMENTS):
        return False
    return lowered.endswith(ALLOWED_SOURCE_SUFFIXES)


def _format_source_chunk(path: str, text: str) -> str:
    safe_path = path.replace("\n", " ")
    return f"// FILE: {safe_path}\n{text}\n"


async def _fetch_npm_weekly_downloads(name: str) -> int:
    url = f"https://api.npmjs.org/downloads/point/last-week/{name}"
    payload = await _http_get(url)
    if not payload:
        return 0
    try:
        return int(payload.get("downloads", 0) or 0)
    except Exception:
        return 0


async def _fetch_pypi_weekly_downloads(name: str) -> int:
    # pypistats is external and may be unavailable; fallback is 0.
    url = f"https://pypistats.org/api/packages/{name}/recent"
    payload = await _http_get(url)
    if not payload:
        return 0
    try:
        data = payload.get("data", {})
        return int(data.get("last_week", 0) or 0)
    except Exception:
        return 0


def _extract_npm_published_at(root_payload: dict[str, Any], version: str) -> str:
    time_data = root_payload.get("time", {})
    if isinstance(time_data, dict):
        value = time_data.get(version, "")
        return str(value or "")
    return ""


def _extract_pypi_published_at(payload: dict[str, Any], version: str) -> str:
    releases = payload.get("releases", {})
    files = releases.get(version, []) if isinstance(releases, dict) else []
    if not files and isinstance(payload.get("urls"), list):
        files = payload.get("urls", [])

    for item in files:
        if not isinstance(item, dict):
            continue
        ts = item.get("upload_time_iso_8601") or item.get("upload_time")
        if ts:
            return str(ts)
    return ""


async def _http_get(url: str) -> dict[str, Any] | None:
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json()
            logger.debug("HTTP %d from %s", resp.status_code, url)
            return None
    except httpx.TimeoutException:
        logger.warning("Timeout fetching %s", url)
        return None
    except Exception as exc:
        logger.warning("HTTP error fetching %s: %s", url, exc)
        return None


async def _http_get_bytes(url: str) -> bytes | None:
    max_bytes = settings.source_download_max_bytes
    try:
        async with httpx.AsyncClient(
            timeout=settings.source_download_timeout_seconds,
            follow_redirects=True,
        ) as client:
            async with client.stream("GET", url) as resp:
                if resp.status_code != 200:
                    logger.debug("Archive fetch HTTP %d from %s", resp.status_code, url)
                    return None

                total = 0
                chunks: list[bytes] = []
                async for chunk in resp.aiter_bytes():
                    total += len(chunk)
                    if total > max_bytes:
                        logger.warning("Archive too large (%d bytes) from %s", total, url)
                        return None
                    chunks.append(chunk)

                return b"".join(chunks)
    except httpx.TimeoutException:
        logger.warning("Timeout fetching archive %s", url)
        return None
    except Exception as exc:
        logger.warning("Archive fetch failed for %s: %s", url, exc)
        return None


def _first_maintainer(maintainers: list[dict[str, Any]]) -> dict[str, Any]:
    if maintainers and isinstance(maintainers[0], dict):
        return maintainers[0]
    return {}
