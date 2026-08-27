"""Add the offline HBX destination catalogue.

Revision ID: 0007
Revises: 0006
"""

from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hbx_destinations",
        sa.Column("code", sa.String(length=20), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("zones", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_hbx_destinations_normalized_name", "hbx_destinations", ["normalized_name"])
    op.create_index("ix_hbx_destinations_country_code", "hbx_destinations", ["country_code"])


def downgrade() -> None:
    op.drop_index("ix_hbx_destinations_country_code", table_name="hbx_destinations")
    op.drop_index("ix_hbx_destinations_normalized_name", table_name="hbx_destinations")
    op.drop_table("hbx_destinations")
