"""Persist travel knowledge nodes and relationships.

Revision ID: 0005
Revises: 0004
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_nodes",
        sa.Column("sequence_id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("node_id", sa.String(160), nullable=False, unique=True),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_knowledge_nodes_entity_type",
        "knowledge_nodes",
        ["entity_type"],
    )
    op.create_index(
        "ix_knowledge_nodes_type_sequence",
        "knowledge_nodes",
        ["entity_type", "sequence_id"],
    )

    op.create_table(
        "knowledge_edges",
        sa.Column("sequence_id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("edge_key", sa.String(64), nullable=False),
        sa.Column(
            "source_id",
            sa.String(160),
            sa.ForeignKey("knowledge_nodes.node_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_type", sa.String(80), nullable=False),
        sa.Column("relationship_type", sa.String(80), nullable=False),
        sa.Column(
            "target_id",
            sa.String(160),
            sa.ForeignKey("knowledge_nodes.node_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("target_type", sa.String(80), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("edge_metadata", sa.JSON(), nullable=False),
        sa.UniqueConstraint("edge_key", name="uq_knowledge_edges_key"),
    )
    op.create_index(
        "ix_knowledge_edges_source_relationship",
        "knowledge_edges",
        ["source_id", "relationship_type"],
    )
    op.create_index(
        "ix_knowledge_edges_target_relationship",
        "knowledge_edges",
        ["target_id", "relationship_type"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_knowledge_edges_target_relationship",
        table_name="knowledge_edges",
    )
    op.drop_index(
        "ix_knowledge_edges_source_relationship",
        table_name="knowledge_edges",
    )
    op.drop_table("knowledge_edges")
    op.drop_index(
        "ix_knowledge_nodes_type_sequence",
        table_name="knowledge_nodes",
    )
    op.drop_index(
        "ix_knowledge_nodes_entity_type",
        table_name="knowledge_nodes",
    )
    op.drop_table("knowledge_nodes")
