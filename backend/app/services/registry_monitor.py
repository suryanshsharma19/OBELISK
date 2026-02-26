"""
Registry Monitor — fetches package metadata from npm and PyPI.

Talks to the public registries via their JSON APIs and normalises
the response into a common dict shape used by the analysis pipeline.

Functions:
    fetch_package_metadata: Fetch + normalise metadata for a package
    fetch_npm_metadata:     npm-specific logic
    fetch_pypi_metadata:    PyPI-specific logic

Usage:
    meta = await fetch_package_metadata("express", "4.18.0", "npm")
"""

from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings
from app.core.exceptions import RegistryError
from app.core.logging import setup_logger

logger = setup_logger(__name__)
settings = get_settings()

# Timeout for outgoing HTTP requests (seconds)
REQUEST_TIMEOUT = 15.0


async def fetch_package_metadata(
    name: str,
    version: str,
    registry: str,
) -> dict[str, Any]:
    """
    Fetch package metadata from the appropriate registry.

    Returns a normalised dict with keys:
        name, version, description, author, license,
        repository, dependencies, scripts, maintainer, ...
    """
    if registry == "npm":
        return await fetch_npm_metadata(name, version)
    elif registry == "pypi":
        return await fetch_pypi_metadata(name, version)
    else:
        raise RegistryError(f"Unsupported registry: {registry}")


# ======================================================================
# npm
# ======================================================================

async def fetch_npm_metadata(name: str, version: str) -> dict[str, Any]:
    """
    Hit the npm registry API.

    Endpoint: https://registry.npmjs.org/{package}/{version}
    Fallback: https://registry.npmjs.org/{package} (latest)
    """
    base = settings.npm_registry_url.rstrip("/")

    # Try version-specific first
    url = f"{base}/{name}/{version}"
    data = await _http_get(url)

    # Fallback to package root if version didn't resolve
    if data is None:
        url = f"{base}/{name}"
        data = await _http_get(url)
        if data is None:
            logger.warning("npm lookup failed for %s@%s", name, version)
            return {"name": name, "version": version}
        # Extract the specific or latest version info
        versions = data.get("versions", {})
        data = versions.get(version, data.get("dist-tags", {}).get("latest", data))
        if isinstance(data, str):
            # dist-tags.latest was a version string, re-fetch
            data = versions.get(data, {"name": name, "version": version})

    return _normalise_npm(data, name, version)


def _normalise_npm(raw: dict[str, Any], name: str, version: str) -> dict[str, Any]:
    """Extract the fields we care about from npm's JSON."""
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
    }


# ======================================================================
# PyPI
# ======================================================================

async def fetch_pypi_metadata(name: str, version: str) -> dict[str, Any]:
    """
    Hit the PyPI JSON API.

    Endpoint: https://pypi.org/pypi/{package}/{version}/json
    Fallback: https://pypi.org/pypi/{package}/json
    """
    base = settings.pypi_registry_url.rstrip("/")

    url = f"{base}/{name}/{version}/json"
    data = await _http_get(url)

    if data is None:
        url = f"{base}/{name}/json"
        data = await _http_get(url)
        if data is None:
            logger.warning("PyPI lookup failed for %s@%s", name, version)
            return {"name": name, "version": version}

    return _normalise_pypi(data, name, version)


def _normalise_pypi(raw: dict[str, Any], name: str, version: str) -> dict[str, Any]:
    """Extract the fields we care about from PyPI's JSON."""
    info = raw.get("info", {})
    return {
        "name": info.get("name", name),
        "version": info.get("version", version),
        "description": info.get("summary", ""),
        "author": {"name": info.get("author", ""), "email": info.get("author_email", "")},
        "license": info.get("license", ""),
        "repository": {"url": info.get("project_urls", {}).get("Source", "")},
        "dependencies": {},  # PyPI doesn't list deps in its JSON API
        "scripts": {},
        "maintainer": {
            "email": info.get("maintainer_email", info.get("author_email", "")),
        },
        "keywords": info.get("keywords", "").split(",") if info.get("keywords") else [],
        "homepage": info.get("home_page", ""),
    }


# ======================================================================
# Shared helpers
# ======================================================================

async def _http_get(url: str) -> dict[str, Any] | None:
    """Fire a GET request, return parsed JSON or None."""
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


def _first_maintainer(maintainers: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the first maintainer dict, or an empty dict."""
    if maintainers and isinstance(maintainers[0], dict):
        return maintainers[0]
    return {}
