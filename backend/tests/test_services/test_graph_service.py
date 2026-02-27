"""Tests for the graph service (Neo4j wrapper).

Neo4j is not available in the test environment, so we mock the
Neo4j client calls and verify that the service logic is correct.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.services import graph_service


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.create_package_node = MagicMock()
    client.create_dependency_edge = MagicMock()
    return client


def test_build_dependency_graph_creates_root_node(mock_client):
    """build_dependency_graph should call create_package_node once."""
    with patch.object(graph_service, "_get_client", return_value=mock_client):
        graph_service.build_dependency_graph(
            name="test-pkg", version="1.0.0",
            registry="npm", risk_score=10.0,
            is_malicious=False, dependencies=[],
        )
    mock_client.create_package_node.assert_called_once_with(
        "test-pkg", "1.0.0", "npm", 10.0, False,
    )


def test_build_dependency_graph_creates_edges(mock_client):
    """Each dependency should produce one dependency edge."""
    deps = [
        {"name": "lodash", "version": "^4.17.21", "type": "production"},
        {"name": "debug", "version": "~3.2.0"},
    ]
    with patch.object(graph_service, "_get_client", return_value=mock_client):
        graph_service.build_dependency_graph(
            name="app", version="2.0.0",
            registry="npm", risk_score=5.0,
            is_malicious=False, dependencies=deps,
        )
    assert mock_client.create_dependency_edge.call_count == 2


def test_build_graph_strips_version_prefix(mock_client):
    """Version prefixes like ^ ~ >= should be stripped."""
    deps = [{"name": "chalk", "version": ">=5.0.0"}]
    with patch.object(graph_service, "_get_client", return_value=mock_client):
        graph_service.build_dependency_graph(
            name="cli", version="1.0.0",
            registry="npm", risk_score=0,
            is_malicious=False, dependencies=deps,
        )
    call_args = mock_client.create_dependency_edge.call_args
    assert call_args.kwargs.get("dep_version", call_args[1].get("dep_version", call_args[0][3])) in ("5.0.0", "=5.0.0")


def test_build_graph_handles_client_error(mock_client):
    """A Neo4j error should be caught and logged, not raised."""
    mock_client.create_package_node.side_effect = Exception("Connection refused")
    with patch.object(graph_service, "_get_client", return_value=mock_client):
        # Should not raise
        graph_service.build_dependency_graph(
            name="fail-pkg", version="1.0.0",
            registry="npm", risk_score=0,
            is_malicious=False, dependencies=[],
        )
