from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CheckoutIntentRow(Base):
    __tablename__ = "commerce_checkout_intents"
    __table_args__ = (
        UniqueConstraint("traveller_id", "idempotency_key", name="uq_checkout_owner_idempotency"),
        CheckConstraint("customer_total >= 0", name="ck_checkout_total_non_negative"),
        CheckConstraint("supplier_net >= 0", name="ck_checkout_supplier_net_non_negative"),
        CheckConstraint("markup >= 0", name="ck_checkout_markup_non_negative"),
        CheckConstraint("taxes_and_fees >= 0", name="ck_checkout_taxes_non_negative"),
        Index("ix_checkout_owner_created", "traveller_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    traveller_id: Mapped[str] = mapped_column(String(255), nullable=False)
    trip_reference: Mapped[str | None] = mapped_column(String(100))
    supplier: Mapped[str] = mapped_column(String(50), nullable=False)
    product_type: Mapped[str] = mapped_column(String(30), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    customer_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    supplier_net: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    markup: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    taxes_and_fees: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PaymentAttemptRow(Base):
    __tablename__ = "commerce_payment_attempts"
    __table_args__ = (
        UniqueConstraint("checkout_id", "idempotency_key", name="uq_payment_checkout_idempotency"),
        CheckConstraint("amount >= 0", name="ck_payment_amount_non_negative"),
        Index("ix_payment_checkout_created", "checkout_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    checkout_id: Mapped[str] = mapped_column(ForeignKey("commerce_checkout_intents.id", ondelete="RESTRICT"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_reference: Mapped[str | None] = mapped_column(String(255), unique=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    failure_code: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SupplierBookingRow(Base):
    __tablename__ = "commerce_supplier_bookings"
    __table_args__ = (
        UniqueConstraint("supplier", "supplier_reference", name="uq_booking_supplier_reference"),
        Index("ix_booking_checkout_created", "checkout_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    checkout_id: Mapped[str] = mapped_column(ForeignKey("commerce_checkout_intents.id", ondelete="RESTRICT"), nullable=False)
    supplier: Mapped[str] = mapped_column(String(50), nullable=False)
    supplier_reference: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    booked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RefundRecordRow(Base):
    __tablename__ = "commerce_refunds"
    __table_args__ = (
        UniqueConstraint("checkout_id", "idempotency_key", name="uq_refund_checkout_idempotency"),
        CheckConstraint("amount >= 0", name="ck_refund_amount_non_negative"),
        Index("ix_refund_checkout_created", "checkout_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    checkout_id: Mapped[str] = mapped_column(ForeignKey("commerce_checkout_intents.id", ondelete="RESTRICT"), nullable=False)
    payment_attempt_id: Mapped[str | None] = mapped_column(ForeignKey("commerce_payment_attempts.id", ondelete="RESTRICT"))
    supplier_booking_id: Mapped[str | None] = mapped_column(ForeignKey("commerce_supplier_bookings.id", ondelete="RESTRICT"))
    provider_reference: Mapped[str | None] = mapped_column(String(255), unique=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
