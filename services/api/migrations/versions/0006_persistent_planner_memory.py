"""Persist account-owned planner conversations and itinerary snapshots.

Revision ID: 0006
Revises: 0005
"""

from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "traveller_profiles",
        sa.Column("traveller_id", sa.String(length=100), primary_key=True),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.Column("updated_at", sa.String(length=40), nullable=False),
        sa.Column("identity", sa.JSON(), nullable=False),
        sa.Column("preferences", sa.JSON(), nullable=False),
        sa.Column("loyalty", sa.JSON(), nullable=False),
        sa.Column("travel_history", sa.JSON(), nullable=False),
    )
    op.create_table(
        "conversation_sessions",
        sa.Column("conversation_id", sa.String(length=36), primary_key=True),
        sa.Column("traveller_id", sa.String(length=100), nullable=True),
        sa.Column("trip_id", sa.String(length=36), nullable=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=40), nullable=False),
        sa.Column("updated_at", sa.String(length=40), nullable=False),
    )
    op.create_index("ix_conversation_sessions_traveller_id", "conversation_sessions", ["traveller_id"])
    op.create_index("ix_conversation_sessions_trip_id", "conversation_sessions", ["trip_id"])
    op.create_index("ix_conversation_sessions_updated_at", "conversation_sessions", ["updated_at"])


def downgrade() -> None:
    op.drop_index("ix_conversation_sessions_updated_at", table_name="conversation_sessions")
    op.drop_index("ix_conversation_sessions_trip_id", table_name="conversation_sessions")
    op.drop_index("ix_conversation_sessions_traveller_id", table_name="conversation_sessions")
    op.drop_table("conversation_sessions")
    op.drop_table("traveller_profiles")
