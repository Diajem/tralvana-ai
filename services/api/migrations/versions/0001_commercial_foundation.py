"""Create the commercial attribution and commission ledger.

Revision ID: 0001
Revises: None
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "commercial_partners",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("website_url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "affiliate_programmes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("partner_id", sa.String(36), sa.ForeignKey("commercial_partners.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("vertical", sa.String(30), nullable=False),
        sa.Column("tracking_template", sa.Text(), nullable=False),
        sa.Column("affiliate_identifier", sa.String(255), nullable=False),
        sa.Column("default_currency", sa.String(3), nullable=False),
        sa.Column("disclosure_text", sa.Text(), nullable=False),
        sa.Column("terms_url", sa.Text()),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("partner_id", "name", name="uq_programme_partner_name"),
    )
    op.create_index("ix_affiliate_programmes_partner_id", "affiliate_programmes", ["partner_id"])
    op.create_index("ix_programme_vertical_status", "affiliate_programmes", ["vertical", "status"])
    op.create_table(
        "outbound_clicks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("programme_id", sa.String(36), sa.ForeignKey("affiliate_programmes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("destination_url", sa.Text(), nullable=False),
        sa.Column("tracking_url", sa.Text(), nullable=False),
        sa.Column("trip_reference", sa.String(100)),
        sa.Column("recommendation_reference", sa.String(100)),
        sa.Column("campaign", sa.String(100)),
        sa.Column("sub_id", sa.String(100)),
        sa.Column("anonymous_session_hash", sa.String(128)),
        sa.Column("attribution_metadata", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_click_programme_occurred", "outbound_clicks", ["programme_id", "occurred_at"])
    op.create_index("ix_click_trip_reference", "outbound_clicks", ["trip_reference"])
    op.create_table(
        "affiliate_conversions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("programme_id", sa.String(36), sa.ForeignKey("affiliate_programmes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("click_id", sa.String(36), sa.ForeignKey("outbound_clicks.id", ondelete="SET NULL")),
        sa.Column("external_reference", sa.String(255), nullable=False),
        sa.Column("gross_value", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("booked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("conversion_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("gross_value >= 0", name="ck_conversion_gross_value_non_negative"),
        sa.UniqueConstraint("programme_id", "external_reference", name="uq_conversion_external_reference"),
    )
    op.create_index("ix_affiliate_conversions_click_id", "affiliate_conversions", ["click_id"])
    op.create_index("ix_conversion_programme_status", "affiliate_conversions", ["programme_id", "status"])
    op.create_table(
        "commission_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("conversion_id", sa.String(36), sa.ForeignKey("affiliate_conversions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("external_reference", sa.String(255), unique=True),
        sa.Column("expected_at", sa.DateTime(timezone=True)),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount >= 0", name="ck_commission_amount_non_negative"),
    )
    op.create_index("ix_commission_records_conversion_id", "commission_records", ["conversion_id"])
    op.create_index("ix_commission_status_created", "commission_records", ["status", "created_at"])


def downgrade() -> None:
    op.drop_table("commission_records")
    op.drop_table("affiliate_conversions")
    op.drop_table("outbound_clicks")
    op.drop_table("affiliate_programmes")
    op.drop_table("commercial_partners")
