"""Tests for the registry monitor service.

These tests mock the HTTP calls so they run offline.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.registry_monitor import (
    fetch_package_metadata,
    fetch_npm_metadata,
    fetch_pypi_metadata,
)
from app.core.exceptions import RegistryError


@pytest.mark.asyncio
async def test_unsupported_registry_raises():
    """Passing an unknown registry should raise RegistryError."""
    with pytest.raises(RegistryError, match="Unsupported registry"):
        await fetch_package_metadata("pkg", "1.0.0", "rubygems")


@pytest.mark.asyncio
async def test_npm_dispatched():
    """npm registry should call fetch_npm_metadata."""
    with patch("app.services.registry_monitor.fetch_npm_metadata", new_callable=AsyncMock) as mock:
        mock.return_value = {"name": "express"}
        result = await fetch_package_metadata("express", "4.18.0", "npm")
        mock.assert_awaited_once_with("express", "4.18.0")
        assert result["name"] == "express"


@pytest.mark.asyncio
async def test_pypi_dispatched():
    """pypi registry should call fetch_pypi_metadata."""
    with patch("app.services.registry_monitor.fetch_pypi_metadata", new_callable=AsyncMock) as mock:
        mock.return_value = {"name": "requests"}
        result = await fetch_package_metadata("requests", "2.31.0", "pypi")
        mock.assert_awaited_once_with("requests", "2.31.0")
        assert result["name"] == "requests"


@pytest.mark.asyncio
async def test_npm_metadata_returns_dict():
    """Mock HTTP for npm and verify normalised output shape."""
    fake_body = {
        "name": "express",
        "version": "4.18.0",
        "description": "Fast web framework",
        "dependencies": {"accepts": "~1.3.8"},
        "scripts": {},
        "maintainers": [{"name": "dougwilson"}],
    }
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = fake_body

    with patch("app.services.registry_monitor._http_get", new_callable=AsyncMock, return_value=fake_body):
        result = await fetch_npm_metadata("express", "4.18.0")
        assert result["name"] == "express"
        assert "dependencies" in result
