"""Add host allow-lists for safe affiliate redirects.

Revision ID: 0002
Revises: 0001
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "affiliate_programmes",
        sa.Column("allowed_destination_hosts", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "affiliate_programmes",
        sa.Column("allowed_tracking_hosts", sa.JSON(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("affiliate_programmes", "allowed_tracking_hosts")
    op.drop_column("affiliate_programmes", "allowed_destination_hosts")
