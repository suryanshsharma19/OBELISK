"""Tests for the sandbox service (simulation mode)."""

import pytest

from app.services.sandbox import run_in_sandbox


@pytest.mark.asyncio
async def test_simulation_returns_expected_keys():
    """Simulated sandbox should return all required telemetry keys."""
    result = await run_in_sandbox("test-pkg", "1.0.0", "npm")
    expected_keys = {
        "network_attempts", "file_writes", "cpu_usage_percent",
        "memory_usage_mb", "process_spawns", "exit_code",
        "execution_time_s", "mode", "logs",
    }
    assert expected_keys.issubset(result.keys())


@pytest.mark.asyncio
async def test_simulation_mode_label():
    """Mode should be 'simulation' when Docker is unavailable."""
    result = await run_in_sandbox("any-pkg", "1.0.0", "npm")
    assert result["mode"] == "simulation"


@pytest.mark.asyncio
async def test_simulation_safe_defaults():
    """Simulated sandbox should report safe / neutral metrics."""
    result = await run_in_sandbox("safe-pkg", "2.0.0", "pypi")
    assert result["network_attempts"] == 0
    assert result["file_writes"] == 0
    assert result["exit_code"] == 0


@pytest.mark.asyncio
async def test_simulation_logs_empty():
    """Simulation should have no execution logs."""
    result = await run_in_sandbox("pkg", "1.0.0", "npm")
    assert result["logs"] == []
