"""Index click attribution used during commission reconciliation.

Revision ID: 0003
Revises: 0002
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_click_programme_sub_id",
        "outbound_clicks",
        ["programme_id", "sub_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_click_programme_sub_id", table_name="outbound_clicks")
