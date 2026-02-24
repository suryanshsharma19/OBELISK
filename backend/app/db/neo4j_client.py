"""
Neo4j driver wrapper for dependency-graph operations.

Provides a connection pool, session helpers, and common Cypher queries
used across the graph_service and gnn_analyzer modules.

Usage:
    client = Neo4jClient()
    client.connect()
    result = client.run_query("MATCH (n) RETURN n LIMIT 5")
    client.close()
"""

from __future__ import annotations

from typing import Any, Optional

from neo4j import GraphDatabase, Session as Neo4jSession

from app.config import get_settings
from app.core.exceptions import DatabaseError
from app.core.logging import setup_logger

logger = setup_logger(__name__)
settings = get_settings()


class Neo4jClient:
    """Thin wrapper around the official Neo4j Python driver."""

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        self._uri = uri or settings.neo4j_uri
        self._user = user or settings.neo4j_user
        self._password = password or settings.neo4j_password
        self._driver = None

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Open the driver connection pool."""
        if self._driver is not None:
            return
        try:
            self._driver = GraphDatabase.driver(
                self._uri,
                auth=(self._user, self._password),
            )
            # Quick connectivity check
            self._driver.verify_connectivity()
            logger.info("Connected to Neo4j at %s", self._uri)
        except Exception as exc:
            logger.error("Neo4j connection failed: %s", exc)
            raise DatabaseError(
                "Could not connect to Neo4j",
                details={"uri": self._uri, "error": str(exc)},
            ) from exc

    def close(self) -> None:
        """Shut down the driver gracefully."""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")

    @property
    def driver(self):
        if self._driver is None:
            self.connect()
        return self._driver

    def get_session(self) -> Neo4jSession:
        """Return a new Neo4j session (caller must close it)."""
        return self.driver.session()

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def run_query(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Execute a Cypher query and return a list of record dicts."""
        try:
            with self.get_session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as exc:
            logger.error("Neo4j query failed: %s | query=%s", exc, query[:120])
            raise DatabaseError(
                "Neo4j query execution failed",
                details={"query": query[:200], "error": str(exc)},
            ) from exc

    # ------------------------------------------------------------------
    # Package-graph operations
    # ------------------------------------------------------------------

    def create_package_node(
        self,
        name: str,
        version: str,
        registry: str,
        risk_score: float = 0.0,
        is_malicious: bool = False,
    ) -> dict[str, Any]:
        """Create (or merge) a Package node and return its properties."""
        query = """
        MERGE (p:Package {name: $name, version: $version, registry: $registry})
        ON CREATE SET
            p.risk_score    = $risk_score,
            p.is_malicious  = $is_malicious,
            p.created_at    = datetime()
        ON MATCH SET
            p.risk_score    = $risk_score,
            p.is_malicious  = $is_malicious
        RETURN p
        """
        rows = self.run_query(query, {
            "name": name,
            "version": version,
            "registry": registry,
            "risk_score": risk_score,
            "is_malicious": is_malicious,
        })
        return rows[0]["p"] if rows else {}

    def create_dependency_edge(
        self,
        parent_name: str,
        parent_version: str,
        dep_name: str,
        dep_version: str,
        dep_type: str = "production",
    ) -> None:
        """Link parent → dependency with a DEPENDS_ON relationship."""
        query = """
        MATCH (parent:Package {name: $parent_name, version: $parent_version})
        MERGE (dep:Package {name: $dep_name, version: $dep_version})
        MERGE (parent)-[r:DEPENDS_ON]->(dep)
        SET r.type = $dep_type
        """
        self.run_query(query, {
            "parent_name": parent_name,
            "parent_version": parent_version,
            "dep_name": dep_name,
            "dep_version": dep_version,
            "dep_type": dep_type,
        })

    def get_dependencies(
        self, name: str, max_depth: int = 5,
    ) -> list[dict[str, Any]]:
        """Traverse the dependency chain up to *max_depth* hops."""
        query = """
        MATCH path = (p:Package {name: $name})-[:DEPENDS_ON*1..$max_depth]->(dep)
        RETURN dep.name        AS name,
               dep.version     AS version,
               dep.risk_score  AS risk_score,
               dep.is_malicious AS is_malicious,
               length(path)    AS depth
        ORDER BY dep.risk_score DESC
        """
        return self.run_query(query, {"name": name, "max_depth": max_depth})

    def find_malicious_in_chain(self, name: str) -> list[dict[str, Any]]:
        """Return any malicious packages reachable from *name*."""
        query = """
        MATCH path = (p:Package {name: $name})-[:DEPENDS_ON*1..5]->(dep)
        WHERE dep.is_malicious = true
        RETURN dep.name       AS name,
               dep.risk_score AS risk_score,
               length(path)   AS depth
        ORDER BY depth ASC
        """
        return self.run_query(query, {"name": name})


# Module-level singleton (lazy-connected)
neo4j_client = Neo4jClient()
