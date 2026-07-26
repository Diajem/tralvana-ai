"""Relational rows for persistent travel knowledge nodes and edges."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from travelos.persistence.base import Base


class KnowledgeNodeRow(Base):
    """Serialized property-graph node."""

    __tablename__ = "knowledge_nodes"

    sequence_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    node_id: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    __table_args__ = (
        Index("ix_knowledge_nodes_entity_type", "entity_type"),
        Index("ix_knowledge_nodes_type_sequence", "entity_type", "sequence_id"),
    )


class KnowledgeEdgeRow(Base):
    """Serialized directed property-graph relationship."""

    __tablename__ = "knowledge_edges"

    sequence_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    edge_key: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("knowledge_nodes.node_id", ondelete="CASCADE"),
        nullable=False,
    )
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(80), nullable=False)
    target_id: Mapped[str] = mapped_column(
        String(160),
        ForeignKey("knowledge_nodes.node_id", ondelete="CASCADE"),
        nullable=False,
    )
    target_type: Mapped[str] = mapped_column(String(80), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    edge_metadata: Mapped[dict] = mapped_column(JSON, nullable=False)

    __table_args__ = (
        UniqueConstraint("edge_key", name="uq_knowledge_edges_key"),
        Index(
            "ix_knowledge_edges_source_relationship",
            "source_id",
            "relationship_type",
        ),
        Index(
            "ix_knowledge_edges_target_relationship",
            "target_id",
            "relationship_type",
        ),
    )
