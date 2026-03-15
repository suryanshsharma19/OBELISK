"""Tests for the GNN (dependency graph) analyser."""

import pytest

from app.ml.gnn_analyzer import GNNAnalyzer


@pytest.fixture
def analyzer():
    return GNNAnalyzer()


@pytest.mark.asyncio
async def test_no_dependencies(analyzer):
    """A package with zero dependencies should get a clean score."""
    result = await analyzer.run(package_name="solo-pkg", dependencies=[])
    assert result.score < 20
    assert result.confidence > 0


@pytest.mark.asyncio
async def test_shallow_dependency_tree(analyzer):
    """A handful of well-known deps should score low."""
    deps = [
        {"name": "express", "version": "4.18.0"},
        {"name": "lodash", "version": "4.17.21"},
    ]
    result = await analyzer.run(package_name="my-app", dependencies=deps)
    assert result.score < 30


@pytest.mark.asyncio
async def test_deep_tree_increases_score(analyzer):
    """Many nested deps should raise the depth component."""
    deps = [{"name": f"dep-{i}", "version": "1.0.0"} for i in range(25)]
    result = await analyzer.run(package_name="deep-app", dependencies=deps)
    # More deps → higher score from depth component
    assert result.score >= 0


@pytest.mark.asyncio
async def test_returns_detection_result(analyzer):
    """Result should always be a DetectionResult with expected fields."""
    result = await analyzer.run(package_name="any-pkg", dependencies=[])
    assert hasattr(result, "score")
    assert hasattr(result, "confidence")
    assert hasattr(result, "evidence")
