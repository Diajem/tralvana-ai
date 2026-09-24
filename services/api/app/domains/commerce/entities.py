from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class CheckoutStatus(str, Enum):
    CREATED = "CREATED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAID = "PAID"
    BOOKING_PENDING = "BOOKING_PENDING"
    BOOKED = "BOOKED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class PaymentStatus(str, Enum):
    CREATED = "CREATED"
    REQUIRES_ACTION = "REQUIRES_ACTION"
    PROCESSING = "PROCESSING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class BookingStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class RefundStatus(str, Enum):
    REQUESTED = "REQUESTED"
    PROCESSING = "PROCESSING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


def _validate_money(amount: Decimal, currency: str) -> str:
    if amount < 0:
        raise ValueError("amount cannot be negative")
    normalized = currency.strip().upper()
    if len(normalized) != 3 or not normalized.isalpha():
        raise ValueError("currency must be a three-letter ISO code")
    return normalized


@dataclass(frozen=True, slots=True)
class CheckoutIntent:
    id: str
    traveller_id: str
    supplier: str
    product_type: str
    idempotency_key: str
    status: CheckoutStatus
    currency: str
    customer_total: Decimal
    supplier_net: Decimal
    markup: Decimal
    taxes_and_fees: Decimal
    created_at: datetime
    updated_at: datetime
    trip_reference: str | None = None

    def __post_init__(self) -> None:
        currency = _validate_money(self.customer_total, self.currency)
        for amount in (self.supplier_net, self.markup, self.taxes_and_fees):
            _validate_money(amount, currency)
        if self.customer_total != self.supplier_net + self.markup + self.taxes_and_fees:
            raise ValueError("checkout total must equal its price components")
        if not self.traveller_id.strip() or not self.idempotency_key.strip():
            raise ValueError("traveller and idempotency key are required")
        object.__setattr__(self, "currency", currency)


@dataclass(frozen=True, slots=True)
class PaymentAttempt:
    id: str
    checkout_id: str
    provider: str
    idempotency_key: str
    status: PaymentStatus
    amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime
    provider_reference: str | None = None
    failure_code: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "currency", _validate_money(self.amount, self.currency))


@dataclass(frozen=True, slots=True)
class SupplierBooking:
    id: str
    checkout_id: str
    supplier: str
    status: BookingStatus
    created_at: datetime
    updated_at: datetime
    supplier_reference: str | None = None
    booked_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class RefundRecord:
    id: str
    checkout_id: str
    idempotency_key: str
    status: RefundStatus
    amount: Decimal
    currency: str
    reason_code: str
    created_at: datetime
    updated_at: datetime
    payment_attempt_id: str | None = None
    supplier_booking_id: str | None = None
    provider_reference: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "currency", _validate_money(self.amount, self.currency))


_CHECKOUT_TRANSITIONS = {
    CheckoutStatus.CREATED: {CheckoutStatus.PAYMENT_PENDING, CheckoutStatus.BOOKING_PENDING, CheckoutStatus.CANCELLED, CheckoutStatus.FAILED},
    CheckoutStatus.PAYMENT_PENDING: {CheckoutStatus.PAID, CheckoutStatus.CANCELLED, CheckoutStatus.FAILED},
    CheckoutStatus.PAID: {CheckoutStatus.BOOKING_PENDING, CheckoutStatus.CANCELLED},
    CheckoutStatus.BOOKING_PENDING: {CheckoutStatus.BOOKED, CheckoutStatus.CANCELLED, CheckoutStatus.FAILED},
    CheckoutStatus.BOOKED: {CheckoutStatus.CANCELLED},
    CheckoutStatus.CANCELLED: set(),
    CheckoutStatus.FAILED: set(),
}


def validate_checkout_transition(current: CheckoutStatus, target: CheckoutStatus) -> None:
    if target not in _CHECKOUT_TRANSITIONS[current]:
        raise ValueError(f"invalid checkout transition: {current.value} -> {target.value}")
