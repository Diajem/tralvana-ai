"""Shared write helpers for deterministic ontology seed modules."""

from ai.intelligence.knowledge.relationships import Relationship, RelationshipType


def add_node(graph, entity, entity_type: str) -> None:
    graph.add_node(entity, entity_type)


def add_edge(
    graph,
    source_id,
    source_type,
    relationship_type,
    target_id,
    target_type,
    weight=1.0,
    **metadata,
) -> None:
    graph.add_edge(
        Relationship(
            source_id,
            source_type,
            relationship_type,
            target_id,
            target_type,
            weight,
            metadata,
        )
    )


R = RelationshipType
