"""Graph Service — higher-level Neo4j operations.

Wraps the raw Neo4j client with business logic for building and
querying the package dependency graph.

Functions:
    build_dependency_graph:  Populate Neo4j from a package analysis
    get_package_graph:       Retrieve the subgraph for a package
    get_graph_stats:         Summary stats about the whole graph
"""

from __future__ import annotations

from typing import Any

from app.core.logging import setup_logger

logger = setup_logger(__name__)


def _get_client():
    """Lazy import to avoid connection issues at module load."""
    from app.db.neo4j_client import neo4j_client
    return neo4j_client


def build_dependency_graph(
    name: str,
    version: str,
    registry: str,
    risk_score: float,
    is_malicious: bool,
    dependencies: list[dict[str, Any]],
) -> None:
    """
    Create / update the package node and all its dependency edges.
    Designed to be called after analysis completes.
    """
    client = _get_client()
    try:
        # Root node
        client.create_package_node(name, version, registry, risk_score, is_malicious)

        # Dependency edges
        for dep in dependencies:
            dep_ver = str(dep.get("version", "0.0.0")).lstrip("^~>=")
            client.create_dependency_edge(
                parent_name=name,
                parent_version=version,
                dep_name=dep["name"],
                dep_version=dep_ver,
                dep_type=dep.get("type", "production"),
            )
        logger.info("Built dependency graph for %s@%s (%d deps)", name, version, len(dependencies))
    except Exception as exc:
        logger.warning("Graph build failed for %s: %s", name, exc)


def get_package_graph(name: str, max_depth: int = 3) -> dict[str, Any]:
    """Return the dependency subgraph for *name*."""
    client = _get_client()
    try:
        deps = client.get_dependencies(name, max_depth=max_depth)
        malicious = client.find_malicious_in_chain(name)
        return {
            "package": name,
            "dependencies": deps,
            "malicious_in_chain": malicious,
            "total_dependencies": len(deps),
        }
    except Exception as exc:
        logger.warning("Graph query failed for %s: %s", name, exc)
        return {"package": name, "dependencies": [], "malicious_in_chain": [], "total_dependencies": 0}


def get_graph_stats() -> dict[str, Any]:
    """Return high-level statistics about the Neo4j graph."""
    client = _get_client()
    try:
        node_count = client.run_query("MATCH (n:Package) RETURN count(n) AS cnt")
        edge_count = client.run_query("MATCH ()-[r:DEPENDS_ON]->() RETURN count(r) AS cnt")
        mal_count = client.run_query("MATCH (n:Package {is_malicious: true}) RETURN count(n) AS cnt")
        return {
            "total_nodes": node_count[0]["cnt"] if node_count else 0,
            "total_edges": edge_count[0]["cnt"] if edge_count else 0,
            "malicious_nodes": mal_count[0]["cnt"] if mal_count else 0,
        }
    except Exception as exc:
        logger.warning("Graph stats query failed: %s", exc)
        return {"total_nodes": 0, "total_edges": 0, "malicious_nodes": 0}
