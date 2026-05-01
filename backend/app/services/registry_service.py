import httpx
import asyncio
from typing import List, Dict, Any
from app.core.logging import setup_logger

logger = setup_logger(__name__)

class RegistryService:
    async def get_package_versions(self, pkg_name: str, limit: int = 10) -> List[str]:
        # For simplicity, supporting just PyPI for now
        url = f"https://pypi.org/pypi/{pkg_name}/json"
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, timeout=5.0)
                if resp.status_code == 200:
                    data = resp.json()
                    releases = list(data.get("releases", {}).keys())
                    # sort versions simply
                    releases.sort(key=lambda s: [int(u) if u.isdigit() else u for u in s.split('.')])
                    return releases[-limit:]
            except Exception as e:
                logger.error(f"Failed to fetch pypi data for {pkg_name}: {e}")
        return []

registry_service = RegistryService()
