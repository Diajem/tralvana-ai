from __future__ import annotations

from typing import Any

from ai.intelligence.knowledge.relationships import Relationship, RelationshipType


class KnowledgeGraph:
    """
    In-memory property graph for the TravelOS Travel Intelligence Layer.

    Nodes are typed entity instances keyed by ID.
    Edges are typed Relationship instances.

    Interface contract: swapping this implementation for Neo4j, ArangoDB, or
    Kuzu in Sprint 4+ requires only replacing this class. All callers (reasoners,
    knowledge service, agents) remain unchanged.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, Any] = {}        # id → entity
        self._node_types: dict[str, str] = {}   # id → entity type name
        self._edges: list[Relationship] = []

    # ------------------------------------------------------------------
    # Node operations
    # ------------------------------------------------------------------

    def add_node(self, entity: Any, entity_type: str) -> None:
        node_id: str = getattr(entity, "id", "")
        if not node_id:
            raise ValueError(f"Entity of type '{entity_type}' has no 'id' attribute.")
        self._nodes[node_id] = entity
        self._node_types[node_id] = entity_type

    def get_node(self, node_id: str) -> Any | None:
        return self._nodes.get(node_id)

    def get_node_type(self, node_id: str) -> str | None:
        return self._node_types.get(node_id)

    def get_nodes_by_type(self, entity_type: str) -> list[Any]:
        return [
            node for nid, node in self._nodes.items()
            if self._node_types.get(nid) == entity_type
        ]

    def find_nodes(self, entity_type: str, **filters: Any) -> list[Any]:
        """Return nodes matching all key=value filters (case-insensitive string compare)."""
        results = []
        for node in self.get_nodes_by_type(entity_type):
            if all(
                str(getattr(node, key, None)).lower() == str(val).lower()
                for key, val in filters.items()
            ):
                results.append(node)
        return results

    def find_node_by_name(self, entity_type: str, name: str) -> Any | None:
        name_lower = name.lower()
        for node in self.get_nodes_by_type(entity_type):
            if getattr(node, "name", "").lower() == name_lower:
                return node
        return None

    def search_nodes(self, entity_type: str, fragment: str) -> list[Any]:
        """Partial name match."""
        frag = fragment.lower()
        return [
            node for node in self.get_nodes_by_type(entity_type)
            if frag in getattr(node, "name", "").lower()
        ]

    # ------------------------------------------------------------------
    # Edge operations
    # ------------------------------------------------------------------

    def add_edge(self, rel: Relationship) -> None:
        self._edges.append(rel)

    def get_outbound_edges(
        self, node_id: str, rel_type: RelationshipType | None = None
    ) -> list[Relationship]:
        return [
            e for e in self._edges
            if e.source_id == node_id
            and (rel_type is None or e.relationship_type == rel_type)
        ]

    def get_inbound_edges(
        self, node_id: str, rel_type: RelationshipType | None = None
    ) -> list[Relationship]:
        return [
            e for e in self._edges
            if e.target_id == node_id
            and (rel_type is None or e.relationship_type == rel_type)
        ]

    def get_all_edges(
        self, node_id: str, rel_type: RelationshipType | None = None
    ) -> list[Relationship]:
        return self.get_outbound_edges(node_id, rel_type) + self.get_inbound_edges(node_id, rel_type)

    def traverse(
        self,
        from_id: str,
        rel_type: RelationshipType,
        depth: int = 1,
    ) -> list[Any]:
        """Walk outbound edges of a given type for up to `depth` hops; return reached nodes."""
        visited: set[str] = {from_id}
        frontier = [from_id]
        results: list[Any] = []

        for _ in range(depth):
            next_frontier: list[str] = []
            for nid in frontier:
                for edge in self.get_outbound_edges(nid, rel_type):
                    if edge.target_id not in visited:
                        visited.add(edge.target_id)
                        next_frontier.append(edge.target_id)
                        node = self.get_node(edge.target_id)
                        if node is not None:
                            results.append(node)
            frontier = next_frontier

        return results

    def neighbourhood(self, node_id: str, depth: int = 1) -> dict[str, list[Any]]:
        """
        Return a subgraph centred on node_id up to `depth` hops in all directions.
        Result is keyed by relationship type value.
        """
        subgraph: dict[str, list[Any]] = {}
        visited: set[str] = {node_id}

        def _expand(nid: str, remaining: int) -> None:
            if remaining == 0:
                return
            for edge in self.get_all_edges(nid):
                partner_id = edge.target_id if edge.source_id == nid else edge.source_id
                rel_key = edge.relationship_type.value
                if partner_id not in visited:
                    visited.add(partner_id)
                    node = self.get_node(partner_id)
                    if node:
                        subgraph.setdefault(rel_key, []).append(node)
                    _expand(partner_id, remaining - 1)

        _expand(node_id, depth)
        return subgraph

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> dict[str, Any]:
        type_counts: dict[str, int] = {}
        for t in self._node_types.values():
            type_counts[t] = type_counts.get(t, 0) + 1
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "nodes_by_type": type_counts,
        }
