"""Persist travel goals and trip plans.

Revision ID: 0004
Revises: 0003
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "travel_goals",
        sa.Column("goal_id", sa.String(36), primary_key=True),
        sa.Column("traveller_id", sa.String(100), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("goal_type", sa.String(40), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("budget", sa.JSON(), nullable=False),
        sa.Column("timeframe", sa.JSON(), nullable=False),
        sa.Column("travellers", sa.JSON(), nullable=False),
        sa.Column("interests", sa.JSON(), nullable=False),
        sa.Column("constraints", sa.JSON(), nullable=False),
        sa.Column("success_criteria", sa.JSON(), nullable=False),
        sa.Column("flexibility", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
        sa.Column("updated_at", sa.String(40), nullable=False),
    )
    op.create_index("ix_travel_goals_traveller_id", "travel_goals", ["traveller_id"])
    op.create_index("ix_travel_goals_status", "travel_goals", ["status"])

    op.create_table(
        "trip_plans",
        sa.Column("trip_id", sa.String(36), primary_key=True),
        sa.Column("traveller_id", sa.String(100)),
        sa.Column("goal_id", sa.String(36)),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("origin", sa.String(150), nullable=False),
        sa.Column("destination", sa.String(150), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("budget", sa.JSON(), nullable=False),
        sa.Column("travellers", sa.JSON(), nullable=False),
        sa.Column("interests", sa.JSON(), nullable=False),
        sa.Column("travel_style", sa.String(30), nullable=False),
        sa.Column("assumptions", sa.JSON(), nullable=False),
        sa.Column("missing_information", sa.JSON(), nullable=False),
        sa.Column("recommended_destinations", sa.JSON(), nullable=False),
        sa.Column("draft_itinerary", sa.JSON(), nullable=False),
        sa.Column("estimated_budget_breakdown", sa.JSON(), nullable=False),
        sa.Column("risks", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.String(40), nullable=False),
        sa.Column("updated_at", sa.String(40), nullable=False),
        sa.Column("recommended_agents", sa.JSON(), nullable=False),
        sa.Column("next_actions", sa.JSON(), nullable=False),
        sa.Column("trip_summary", sa.Text(), nullable=False),
    )
    op.create_index("ix_trip_plans_traveller_id", "trip_plans", ["traveller_id"])
    op.create_index("ix_trip_plans_goal_id", "trip_plans", ["goal_id"])
    op.create_index("ix_trip_plans_status", "trip_plans", ["status"])


def downgrade() -> None:
    op.drop_index("ix_trip_plans_status", table_name="trip_plans")
    op.drop_index("ix_trip_plans_goal_id", table_name="trip_plans")
    op.drop_index("ix_trip_plans_traveller_id", table_name="trip_plans")
    op.drop_table("trip_plans")
    op.drop_index("ix_travel_goals_status", table_name="travel_goals")
    op.drop_index("ix_travel_goals_traveller_id", table_name="travel_goals")
    op.drop_table("travel_goals")
