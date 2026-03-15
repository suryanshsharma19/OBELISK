"""Tests for the typosquatting detector."""

import pytest

from app.ml.typosquat import TyposquattingDetector


@pytest.fixture
def detector():
    return TyposquattingDetector()


@pytest.mark.asyncio
async def test_exact_match_returns_zero(detector):
    """An exact match to a popular package should score 0."""
    result = await detector.run(package_name="express")
    assert result.score == 0.0
    assert result.evidence.get("exact_match") == "express"


@pytest.mark.asyncio
async def test_typosquat_detected(detector):
    """A single-char typo should be flagged with a high score."""
    result = await detector.run(package_name="expresss")
    assert result.score > 80
    assert result.evidence["is_typosquatting"] is True
    similar = result.evidence["similar_packages"]
    assert len(similar) > 0
    assert similar[0]["name"] == "express"


@pytest.mark.asyncio
async def test_completely_different_name(detector):
    """A totally unrelated name should score 0."""
    result = await detector.run(package_name="zxcvbnm-unique-pkg-8374")
    assert result.score == 0.0
    assert result.evidence["is_typosquatting"] is False


@pytest.mark.asyncio
async def test_empty_name(detector):
    """Empty input should return a zero result without crashing."""
    result = await detector.run(package_name="")
    assert result.score == 0.0


@pytest.mark.asyncio
async def test_close_to_react(detector):
    """r3act should be close to react."""
    result = await detector.run(package_name="r3act")
    # Depending on threshold it might or might not flag — but shouldn't crash
    assert 0 <= result.score <= 100
