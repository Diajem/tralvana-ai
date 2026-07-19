from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class PartnerRow(Base):
    __tablename__ = "commercial_partners"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    website_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AffiliateProgrammeRow(Base):
    __tablename__ = "affiliate_programmes"
    __table_args__ = (
        UniqueConstraint("partner_id", "name", name="uq_programme_partner_name"),
        Index("ix_programme_vertical_status", "vertical", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    partner_id: Mapped[str] = mapped_column(
        ForeignKey("commercial_partners.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    vertical: Mapped[str] = mapped_column(String(30), nullable=False)
    tracking_template: Mapped[str] = mapped_column(Text, nullable=False)
    affiliate_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    default_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    disclosure_text: Mapped[str] = mapped_column(Text, nullable=False)
    terms_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    partner: Mapped[PartnerRow] = relationship()


class OutboundClickRow(Base):
    __tablename__ = "outbound_clicks"
    __table_args__ = (
        Index("ix_click_programme_occurred", "programme_id", "occurred_at"),
        Index("ix_click_trip_reference", "trip_reference"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    programme_id: Mapped[str] = mapped_column(
        ForeignKey("affiliate_programmes.id", ondelete="RESTRICT"), nullable=False
    )
    destination_url: Mapped[str] = mapped_column(Text, nullable=False)
    tracking_url: Mapped[str] = mapped_column(Text, nullable=False)
    trip_reference: Mapped[str | None] = mapped_column(String(100))
    recommendation_reference: Mapped[str | None] = mapped_column(String(100))
    campaign: Mapped[str | None] = mapped_column(String(100))
    sub_id: Mapped[str | None] = mapped_column(String(100))
    anonymous_session_hash: Mapped[str | None] = mapped_column(String(128))
    attribution_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AffiliateConversionRow(Base):
    __tablename__ = "affiliate_conversions"
    __table_args__ = (
        UniqueConstraint("programme_id", "external_reference", name="uq_conversion_external_reference"),
        CheckConstraint("gross_value >= 0", name="ck_conversion_gross_value_non_negative"),
        Index("ix_conversion_programme_status", "programme_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    programme_id: Mapped[str] = mapped_column(
        ForeignKey("affiliate_programmes.id", ondelete="RESTRICT"), nullable=False
    )
    click_id: Mapped[str | None] = mapped_column(
        ForeignKey("outbound_clicks.id", ondelete="SET NULL"), index=True
    )
    external_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    gross_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    booked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    conversion_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CommissionRecordRow(Base):
    __tablename__ = "commission_records"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_commission_amount_non_negative"),
        Index("ix_commission_status_created", "status", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    conversion_id: Mapped[str] = mapped_column(
        ForeignKey("affiliate_conversions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(255), unique=True)
    expected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
