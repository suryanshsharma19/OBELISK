#!/usr/bin/env python3
"""Populate the popular packages list for the typosquatting detector."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from app.core.logging import setup_logger

logger = setup_logger("populate_packages")

OUTPUT_FILE = Path("ml_models/datasets/popular_packages.json")

# npm top packages endpoint (unofficial but widely used)
NPM_SEARCH_URL = "https://registry.npmjs.org/-/v1/search?text=boost-exact:true&size=250&quality=0.0&popularity=1.0&maintenance=0.0"

# PyPI top packages (from hugovk's top-pypi-packages dataset)
PYPI_TOP_URL = "https://hugovk.github.io/top-pypi-packages/top-pypi-packages-30-days.min.json"


async def fetch_npm_popular() -> list[str]:
    packages = []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(NPM_SEARCH_URL)
            if resp.status_code == 200:
                data = resp.json()
                for obj in data.get("objects", []):
                    name = obj.get("package", {}).get("name")
                    if name:
                        packages.append(name)
                logger.info("Fetched %d npm packages", len(packages))
    except Exception as exc:
        logger.warning("Failed to fetch npm packages: %s", exc)
    return packages


async def fetch_pypi_popular() -> list[str]:
    packages = []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(PYPI_TOP_URL)
            if resp.status_code == 200:
                data = resp.json()
                for row in data.get("rows", [])[:250]:
                    name = row.get("project")
                    if name:
                        packages.append(name)
                logger.info("Fetched %d PyPI packages", len(packages))
    except Exception as exc:
        logger.warning("Failed to fetch PyPI packages: %s", exc)
    return packages


async def main() -> None:
    logger.info("Fetching popular packages from registries …")

    import asyncio
    npm_pkgs, pypi_pkgs = await asyncio.gather(
        fetch_npm_popular(),
        fetch_pypi_popular(),
    )

    # Deduplicate and sort
    all_packages = sorted(set(npm_pkgs + pypi_pkgs))
    logger.info("Total unique packages: %d", len(all_packages))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(all_packages, indent=2))
    logger.info("Written to %s", OUTPUT_FILE)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
