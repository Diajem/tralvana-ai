"""SQLAlchemy-backed implementation of the TravelOS knowledge graph contract."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from ai.intelligence.knowledge.entities import (
    Airline,
    Airport,
    Attraction,
    City,
    Country,
    Cuisine,
    Currency,
    Event,
    FootballClub,
    Hotel,
    Language,
    Museum,
    RailStation,
    Region,
    Restaurant,
    SportsVenue,
    Transport,
    TravelSeason,
    TravellerDNA,
    VisaRequirement,
    Weather,
)
from ai.intelligence.knowledge.knowledge_graph import KnowledgeGraph
from ai.intelligence.knowledge.relationships import Relationship, RelationshipType
from travelos.persistence.knowledge_orm import KnowledgeEdgeRow, KnowledgeNodeRow

_ENTITY_CLASSES: dict[str, type] = {
    entity_class.__name__: entity_class
    for entity_class in (
        Airline,
        Airport,
        Attraction,
        City,
        Country,
        Cuisine,
        Currency,
        Event,
        FootballClub,
        Hotel,
        Language,
        Museum,
        RailStation,
        Region,
        Restaurant,
        SportsVenue,
        Transport,
        TravelSeason,
        TravellerDNA,
        VisaRequirement,
        Weather,
    )
}

_OBSOLETE_BASELINE_NODE_IDS = {
    "club_gamba",
    "venue_panasonic",
}


class SqlAlchemyKnowledgeGraph:
    """Persistent property graph sharing Tralvana's configured SQL database."""

    def __init__(self, factory: sessionmaker[Session]) -> None:
        self._factory = factory

    def seed_from(self, source: KnowledgeGraph) -> None:
        """Upsert a complete baseline graph in one transaction."""
        with self._factory.begin() as session:
            # Baseline corrections occasionally retire a wrongly identified
            # entity. Upserts cannot remove those historical rows, so delete
            # only explicitly deprecated seed IDs; FK cascades remove their
            # obsolete relationships without touching runtime-added knowledge.
            session.execute(
                delete(KnowledgeNodeRow).where(
                    KnowledgeNodeRow.node_id.in_(
                        _OBSOLETE_BASELINE_NODE_IDS
                    )
                )
            )
            existing_nodes = {
                row.node_id: row
                for row in session.scalars(select(KnowledgeNodeRow)).all()
            }
            for entity, entity_type in source.iter_nodes():
                node_id, payload = _serialize_entity(entity, entity_type)
                row = existing_nodes.get(node_id)
                if row is None:
                    row = KnowledgeNodeRow(
                        node_id=node_id,
                        entity_type=entity_type,
                        payload=payload,
                    )
                    session.add(row)
                    existing_nodes[node_id] = row
                else:
                    row.entity_type = entity_type
                    row.payload = payload

            # The standard session factory disables autoflush. Persist every
            # node before queuing edges so enforced foreign keys never see a
            # relationship before its endpoints.
            session.flush()

            existing_edges = set(
                session.scalars(select(KnowledgeEdgeRow.edge_key)).all()
            )
            for relationship in source.iter_edges():
                edge_key = _edge_key(relationship)
                if edge_key in existing_edges:
                    continue
                session.add(_edge_row(relationship, edge_key))
                existing_edges.add(edge_key)

    def add_node(self, entity: Any, entity_type: str) -> None:
        node_id, payload = _serialize_entity(entity, entity_type)
        with self._factory.begin() as session:
            row = session.scalar(
                select(KnowledgeNodeRow).where(KnowledgeNodeRow.node_id == node_id)
            )
            if row is None:
                session.add(
                    KnowledgeNodeRow(
                        node_id=node_id,
                        entity_type=entity_type,
                        payload=payload,
                    )
                )
            else:
                row.entity_type = entity_type
                row.payload = payload

    def get_node(self, node_id: str) -> Any | None:
        with self._factory() as session:
            row = session.scalar(
                select(KnowledgeNodeRow).where(KnowledgeNodeRow.node_id == node_id)
            )
            return _deserialize_entity(row) if row else None

    def get_node_type(self, node_id: str) -> str | None:
        with self._factory() as session:
            return session.scalar(
                select(KnowledgeNodeRow.entity_type).where(
                    KnowledgeNodeRow.node_id == node_id
                )
            )

    def get_nodes_by_type(self, entity_type: str) -> list[Any]:
        with self._factory() as session:
            rows = session.scalars(
                select(KnowledgeNodeRow)
                .where(KnowledgeNodeRow.entity_type == entity_type)
                .order_by(KnowledgeNodeRow.sequence_id)
            ).all()
            return [_deserialize_entity(row) for row in rows]

    def find_nodes(self, entity_type: str, **filters: Any) -> list[Any]:
        return [
            node
            for node in self.get_nodes_by_type(entity_type)
            if all(
                str(getattr(node, key, None)).lower() == str(value).lower()
                for key, value in filters.items()
            )
        ]

    def find_node_by_name(self, entity_type: str, name: str) -> Any | None:
        name_lower = name.lower()
        return next(
            (
                node
                for node in self.get_nodes_by_type(entity_type)
                if getattr(node, "name", "").lower() == name_lower
            ),
            None,
        )

    def search_nodes(self, entity_type: str, fragment: str) -> list[Any]:
        fragment_lower = fragment.lower()
        return [
            node
            for node in self.get_nodes_by_type(entity_type)
            if fragment_lower in getattr(node, "name", "").lower()
        ]

    def add_edge(self, relationship: Relationship) -> None:
        edge_key = _edge_key(relationship)
        with self._factory.begin() as session:
            exists = session.scalar(
                select(KnowledgeEdgeRow.sequence_id).where(
                    KnowledgeEdgeRow.edge_key == edge_key
                )
            )
            if exists is None:
                session.add(_edge_row(relationship, edge_key))

    def get_outbound_edges(
        self,
        node_id: str,
        rel_type: RelationshipType | None = None,
    ) -> list[Relationship]:
        return self._load_edges(KnowledgeEdgeRow.source_id, node_id, rel_type)

    def get_inbound_edges(
        self,
        node_id: str,
        rel_type: RelationshipType | None = None,
    ) -> list[Relationship]:
        return self._load_edges(KnowledgeEdgeRow.target_id, node_id, rel_type)

    def get_all_edges(
        self,
        node_id: str,
        rel_type: RelationshipType | None = None,
    ) -> list[Relationship]:
        edges = self.get_outbound_edges(node_id, rel_type)
        edges.extend(self.get_inbound_edges(node_id, rel_type))
        return edges

    def traverse(
        self,
        from_id: str,
        rel_type: RelationshipType,
        depth: int = 1,
    ) -> list[Any]:
        visited = {from_id}
        frontier = [from_id]
        results: list[Any] = []
        for _ in range(depth):
            next_frontier: list[str] = []
            for node_id in frontier:
                for edge in self.get_outbound_edges(node_id, rel_type):
                    if edge.target_id in visited:
                        continue
                    visited.add(edge.target_id)
                    next_frontier.append(edge.target_id)
                    node = self.get_node(edge.target_id)
                    if node is not None:
                        results.append(node)
            frontier = next_frontier
        return results

    def neighbourhood(self, node_id: str, depth: int = 1) -> dict[str, list[Any]]:
        subgraph: dict[str, list[Any]] = {}
        visited = {node_id}

        def expand(current_id: str, remaining: int) -> None:
            if remaining == 0:
                return
            for edge in self.get_all_edges(current_id):
                partner_id = (
                    edge.target_id
                    if edge.source_id == current_id
                    else edge.source_id
                )
                if partner_id in visited:
                    continue
                visited.add(partner_id)
                node = self.get_node(partner_id)
                if node is not None:
                    subgraph.setdefault(edge.relationship_type.value, []).append(node)
                expand(partner_id, remaining - 1)

        expand(node_id, depth)
        return subgraph

    def stats(self) -> dict[str, Any]:
        with self._factory() as session:
            total_nodes = session.scalar(
                select(func.count()).select_from(KnowledgeNodeRow)
            )
            total_edges = session.scalar(
                select(func.count()).select_from(KnowledgeEdgeRow)
            )
            type_counts = dict(
                session.execute(
                    select(
                        KnowledgeNodeRow.entity_type,
                        func.count(KnowledgeNodeRow.sequence_id),
                    ).group_by(KnowledgeNodeRow.entity_type)
                ).all()
            )
        return {
            "total_nodes": int(total_nodes or 0),
            "total_edges": int(total_edges or 0),
            "nodes_by_type": type_counts,
        }

    def _load_edges(
        self,
        column: Any,
        node_id: str,
        rel_type: RelationshipType | None,
    ) -> list[Relationship]:
        statement = select(KnowledgeEdgeRow).where(column == node_id)
        if rel_type is not None:
            statement = statement.where(
                KnowledgeEdgeRow.relationship_type == rel_type.value
            )
        statement = statement.order_by(KnowledgeEdgeRow.sequence_id)
        with self._factory() as session:
            rows = session.scalars(statement).all()
            return [_relationship(row) for row in rows]


def _serialize_entity(entity: Any, entity_type: str) -> tuple[str, dict]:
    if entity_type not in _ENTITY_CLASSES:
        raise ValueError(f"Unsupported knowledge entity type '{entity_type}'.")
    node_id = getattr(entity, "id", "")
    if not node_id:
        raise ValueError(f"Entity of type '{entity_type}' has no 'id' attribute.")
    if not is_dataclass(entity):
        raise TypeError(f"Knowledge entity '{node_id}' must be a dataclass.")
    return str(node_id), asdict(entity)


def _deserialize_entity(row: KnowledgeNodeRow) -> Any:
    entity_class = _ENTITY_CLASSES.get(row.entity_type)
    if entity_class is None:
        raise ValueError(f"Unsupported stored entity type '{row.entity_type}'.")
    return entity_class(**dict(row.payload))


def _edge_key(relationship: Relationship) -> str:
    canonical = json.dumps(
        {
            "source_id": relationship.source_id,
            "source_type": relationship.source_type,
            "relationship_type": relationship.relationship_type.value,
            "target_id": relationship.target_id,
            "target_type": relationship.target_type,
            "weight": relationship.weight,
            "metadata": relationship.metadata,
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _edge_row(
    relationship: Relationship,
    edge_key: str,
) -> KnowledgeEdgeRow:
    return KnowledgeEdgeRow(
        edge_key=edge_key,
        source_id=relationship.source_id,
        source_type=relationship.source_type,
        relationship_type=relationship.relationship_type.value,
        target_id=relationship.target_id,
        target_type=relationship.target_type,
        weight=relationship.weight,
        edge_metadata=dict(relationship.metadata),
    )


def _relationship(row: KnowledgeEdgeRow) -> Relationship:
    return Relationship(
        source_id=row.source_id,
        source_type=row.source_type,
        relationship_type=RelationshipType(row.relationship_type),
        target_id=row.target_id,
        target_type=row.target_type,
        weight=row.weight,
        metadata=dict(row.edge_metadata),
    )
