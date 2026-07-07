from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ai.intelligence.knowledge.relationships import Relationship, RelationshipType

if TYPE_CHECKING:
    from ai.intelligence.knowledge.knowledge_graph import KnowledgeGraph


class KnowledgeService:
    """
    High-level facade over KnowledgeGraph.

    Responsibilities:
    - Load entities by type
    - Find relationships (inbound / outbound / both directions)
    - Expand a node's neighbourhood (subgraph up to N hops)
    - Retrieve connected entities of a specific type

    Design intent: replacing KnowledgeGraph with a Neo4j or Kuzu driver
    in Sprint 4 only requires updating KnowledgeGraph — all callers of
    KnowledgeService remain unchanged.
    """

    def __init__(self, graph: KnowledgeGraph) -> None:
        self._graph = graph

    # ------------------------------------------------------------------
    # Entity access
    # ------------------------------------------------------------------

    def load_entities(self, entity_type: str) -> list[Any]:
        """Return all nodes of a given entity type."""
        return self._graph.get_nodes_by_type(entity_type)

    def find_entity(self, entity_type: str, name: str) -> Any | None:
        """Case-insensitive exact name lookup."""
        return self._graph.find_node_by_name(entity_type, name)

    def find_entity_by_id(self, node_id: str) -> Any | None:
        """Direct ID lookup."""
        return self._graph.get_node(node_id)

    def search_entities(self, entity_type: str, fragment: str) -> list[Any]:
        """Partial name search."""
        return self._graph.search_nodes(entity_type, fragment)

    # ------------------------------------------------------------------
    # Relationship access
    # ------------------------------------------------------------------

    def find_relationships(
        self,
        node_id: str,
        rel_type: RelationshipType | None = None,
        direction: str = "both",   # "outbound" | "inbound" | "both"
    ) -> list[Relationship]:
        if direction == "outbound":
            return self._graph.get_outbound_edges(node_id, rel_type)
        if direction == "inbound":
            return self._graph.get_inbound_edges(node_id, rel_type)
        return self._graph.get_all_edges(node_id, rel_type)

    def get_connected_entities(
        self,
        node_id: str,
        target_type: str | None = None,
        rel_type: RelationshipType | None = None,
        direction: str = "both",
    ) -> list[Any]:
        """
        Return all entities reachable from node_id via one hop.
        Optionally filter by target entity type and/or relationship type.
        """
        edges = self.find_relationships(node_id, rel_type, direction)
        results: list[Any] = []
        for edge in edges:
            partner_id = edge.target_id if edge.source_id == node_id else edge.source_id
            node = self._graph.get_node(partner_id)
            if node is None:
                continue
            if target_type and self._graph.get_node_type(partner_id) != target_type:
                continue
            results.append(node)
        return results

    # ------------------------------------------------------------------
    # Graph expansion
    # ------------------------------------------------------------------

    def expand_graph(self, node_id: str, depth: int = 2) -> dict[str, Any]:
        """
        Return a subgraph dict centred on node_id.

        Shape:
        {
          "center": {"id": ..., "type": ..., "entity": ...},
          "neighbourhood": {rel_type_value: [entity, ...]},
          "depth": depth,
          "node_count": N,
        }
        """
        center = self._graph.get_node(node_id)
        center_type = self._graph.get_node_type(node_id)
        neighbourhood = self._graph.neighbourhood(node_id, depth)
        node_count = sum(len(v) for v in neighbourhood.values())
        return {
            "center": {"id": node_id, "type": center_type, "entity": center},
            "neighbourhood": neighbourhood,
            "depth": depth,
            "node_count": node_count + 1,  # +1 for center
        }

    # ------------------------------------------------------------------
    # Mutation (for runtime graph extension)
    # ------------------------------------------------------------------

    def add_entity(self, entity: Any, entity_type: str) -> None:
        self._graph.add_node(entity, entity_type)

    def add_relationship(self, rel: Relationship) -> None:
        self._graph.add_edge(rel)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> dict[str, Any]:
        return self._graph.stats()
