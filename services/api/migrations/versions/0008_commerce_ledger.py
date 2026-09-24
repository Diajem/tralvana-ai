"""Add durable checkout, payment, supplier-booking and refund records.

Revision ID: 0008
Revises: 0007
"""

from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "commerce_checkout_intents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("traveller_id", sa.String(255), nullable=False),
        sa.Column("trip_reference", sa.String(100)),
        sa.Column("supplier", sa.String(50), nullable=False),
        sa.Column("product_type", sa.String(30), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("customer_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("supplier_net", sa.Numeric(14, 2), nullable=False),
        sa.Column("markup", sa.Numeric(14, 2), nullable=False),
        sa.Column("taxes_and_fees", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("traveller_id", "idempotency_key", name="uq_checkout_owner_idempotency"),
        sa.CheckConstraint("customer_total >= 0", name="ck_checkout_total_non_negative"),
        sa.CheckConstraint("supplier_net >= 0", name="ck_checkout_supplier_net_non_negative"),
        sa.CheckConstraint("markup >= 0", name="ck_checkout_markup_non_negative"),
        sa.CheckConstraint("taxes_and_fees >= 0", name="ck_checkout_taxes_non_negative"),
    )
    op.create_index("ix_checkout_owner_created", "commerce_checkout_intents", ["traveller_id", "created_at"])
    op.create_table(
        "commerce_payment_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("checkout_id", sa.String(36), sa.ForeignKey("commerce_checkout_intents.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("provider_reference", sa.String(255), unique=True),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("failure_code", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("checkout_id", "idempotency_key", name="uq_payment_checkout_idempotency"),
        sa.CheckConstraint("amount >= 0", name="ck_payment_amount_non_negative"),
    )
    op.create_index("ix_payment_checkout_created", "commerce_payment_attempts", ["checkout_id", "created_at"])
    op.create_table(
        "commerce_supplier_bookings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("checkout_id", sa.String(36), sa.ForeignKey("commerce_checkout_intents.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("supplier", sa.String(50), nullable=False),
        sa.Column("supplier_reference", sa.String(255)),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("booked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("supplier", "supplier_reference", name="uq_booking_supplier_reference"),
    )
    op.create_index("ix_booking_checkout_created", "commerce_supplier_bookings", ["checkout_id", "created_at"])
    op.create_table(
        "commerce_refunds",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("checkout_id", sa.String(36), sa.ForeignKey("commerce_checkout_intents.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("payment_attempt_id", sa.String(36), sa.ForeignKey("commerce_payment_attempts.id", ondelete="RESTRICT")),
        sa.Column("supplier_booking_id", sa.String(36), sa.ForeignKey("commerce_supplier_bookings.id", ondelete="RESTRICT")),
        sa.Column("provider_reference", sa.String(255), unique=True),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("reason_code", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("checkout_id", "idempotency_key", name="uq_refund_checkout_idempotency"),
        sa.CheckConstraint("amount >= 0", name="ck_refund_amount_non_negative"),
    )
    op.create_index("ix_refund_checkout_created", "commerce_refunds", ["checkout_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_refund_checkout_created", table_name="commerce_refunds")
    op.drop_table("commerce_refunds")
    op.drop_index("ix_booking_checkout_created", table_name="commerce_supplier_bookings")
    op.drop_table("commerce_supplier_bookings")
    op.drop_index("ix_payment_checkout_created", table_name="commerce_payment_attempts")
    op.drop_table("commerce_payment_attempts")
    op.drop_index("ix_checkout_owner_created", table_name="commerce_checkout_intents")
    op.drop_table("commerce_checkout_intents")
