from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid4())


class PartnerStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"


class ProgrammeStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"


class CommercialVertical(str, Enum):
    FLIGHTS = "FLIGHTS"
    ACCOMMODATION = "ACCOMMODATION"
    ACTIVITIES = "ACTIVITIES"
    INSURANCE = "INSURANCE"
    CARS = "CARS"
    PARKING = "PARKING"
    ESIM = "ESIM"
    RETAIL = "RETAIL"
    TRANSFERS = "TRANSFERS"
    PACKAGES = "PACKAGES"
    OTHER = "OTHER"


class ConversionStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class CommissionStatus(str, Enum):
    EXPECTED = "EXPECTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAID = "PAID"


@dataclass(slots=True)
class Partner:
    slug: str
    name: str
    website_url: str
    status: PartnerStatus = PartnerStatus.PENDING
    id: str = field(default_factory=new_id)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class AffiliateProgramme:
    partner_id: str
    name: str
    vertical: CommercialVertical
    tracking_template: str
    affiliate_identifier: str
    allowed_destination_hosts: tuple[str, ...] = ()
    allowed_tracking_hosts: tuple[str, ...] = ()
    default_currency: str = "GBP"
    disclosure_text: str = "Tralvana may earn a commission from this link."
    terms_url: str | None = None
    status: ProgrammeStatus = ProgrammeStatus.DRAFT
    id: str = field(default_factory=new_id)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class OutboundClick:
    programme_id: str
    destination_url: str
    tracking_url: str
    trip_reference: str | None = None
    recommendation_reference: str | None = None
    campaign: str | None = None
    sub_id: str | None = None
    anonymous_session_hash: str | None = None
    attribution_metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=new_id)
    occurred_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class AffiliateConversion:
    programme_id: str
    external_reference: str
    gross_value: Decimal
    currency: str
    click_id: str | None = None
    status: ConversionStatus = ConversionStatus.PENDING
    booked_at: datetime = field(default_factory=utc_now)
    confirmed_at: datetime | None = None
    conversion_metadata: dict = field(default_factory=dict)
    id: str = field(default_factory=new_id)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class CommissionRecord:
    conversion_id: str
    amount: Decimal
    currency: str
    status: CommissionStatus = CommissionStatus.EXPECTED
    external_reference: str | None = None
    expected_at: datetime | None = None
    approved_at: datetime | None = None
    paid_at: datetime | None = None
    id: str = field(default_factory=new_id)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
