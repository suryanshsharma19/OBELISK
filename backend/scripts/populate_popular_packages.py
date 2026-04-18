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
TARGET_SIZE = 10_000
NPM_BATCH_SIZE = 250

# npm top packages endpoint (supports pagination via "from")
NPM_SEARCH_URL = "https://registry.npmjs.org/-/v1/search"

# PyPI top packages (from hugovk's top-pypi-packages dataset)
PYPI_TOP_URL = "https://hugovk.github.io/top-pypi-packages/top-pypi-packages-30-days.min.json"


async def fetch_npm_popular(limit: int = 5000) -> list[str]:
    packages = []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            offset = 0
            while len(packages) < limit:
                resp = await client.get(
                    NPM_SEARCH_URL,
                    params={
                        "text": "",
                        "size": NPM_BATCH_SIZE,
                        "from": offset,
                        "quality": 0.0,
                        "popularity": 1.0,
                        "maintenance": 0.0,
                    },
                )
                if resp.status_code != 200:
                    break

                data = resp.json()
                objects = data.get("objects", [])
                if not objects:
                    break

                for obj in objects:
                    name = obj.get("package", {}).get("name")
                    if name:
                        packages.append(name)
                    if len(packages) >= limit:
                        break

                offset += NPM_BATCH_SIZE

            logger.info("Fetched %d npm packages", len(packages))
    except Exception as exc:
        logger.warning("Failed to fetch npm packages: %s", exc)
    return packages


async def fetch_pypi_popular(limit: int = 5000) -> list[str]:
    packages = []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(PYPI_TOP_URL)
            if resp.status_code == 200:
                data = resp.json()
                for row in data.get("rows", [])[:limit]:
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
        fetch_npm_popular(limit=TARGET_SIZE),
        fetch_pypi_popular(limit=TARGET_SIZE),
    )

    # Deduplicate and sort
    all_packages = sorted(set(npm_pkgs + pypi_pkgs))[:TARGET_SIZE]
    logger.info("Total unique packages: %d", len(all_packages))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(all_packages, indent=2))
    logger.info("Written to %s", OUTPUT_FILE)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
