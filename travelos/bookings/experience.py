"""Provider-neutral experience discovery and transaction records.

The contract deliberately contains no Viator field names. Search and
availability are read-only; holds, bookings and cancellations are separate
transactional operations and must never be cached or retried as discovery.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ExperiencePassengerGroup:
    age_band: str
    count: int


@dataclass(frozen=True)
class ExperienceSearchCommand:
    destination: str
    start_date: str
    end_date: str
    currency: str
    passenger_groups: tuple[ExperiencePassengerGroup, ...]


@dataclass(frozen=True)
class ExperienceAvailabilityCommand:
    product_reference: str
    option_reference: str
    travel_date: str
    currency: str
    passenger_groups: tuple[ExperiencePassengerGroup, ...]


@dataclass(frozen=True)
class ExperienceAvailabilityQuote:
    provider_name: str
    product_reference: str
    option_reference: str
    status: str
    total: float
    currency: str
    start_time: str = ""
    cancellation_summary: str = ""


@dataclass(frozen=True)
class ExperienceHoldCommand:
    availability_reference: str
    client_reference: str
    customer_checkout_intent: bool


@dataclass(frozen=True)
class ExperienceHold:
    provider_name: str
    hold_reference: str
    client_reference: str
    status: str
    total: float
    currency: str
    availability_expires_at: str = ""
    pricing_expires_at: str = ""


@dataclass(frozen=True)
class ExperienceBookingCommand:
    hold_reference: str
    client_reference: str
    customer_approved: bool
    expected_total: float
    expected_currency: str


@dataclass(frozen=True)
class ExperienceBooking:
    provider_name: str
    supplier_reference: str
    client_reference: str
    status: str
    total: float
    currency: str
    voucher_reference: str = ""


@dataclass(frozen=True)
class ExperienceCancellationQuote:
    provider_name: str
    supplier_reference: str
    status: str
    refund_amount: float
    refund_percentage: float
    currency: str


@dataclass(frozen=True)
class ExperienceCancellationCommand:
    supplier_reference: str
    reason_reference: str
    customer_approved: bool


@dataclass(frozen=True)
class ExperienceCancellation:
    provider_name: str
    supplier_reference: str
    status: str
    refund_amount: float
    currency: str


class ExperienceProvider(Protocol):
    def search(self, command: ExperienceSearchCommand) -> tuple[dict, ...]: ...

    def check_availability(
        self, command: ExperienceAvailabilityCommand
    ) -> ExperienceAvailabilityQuote: ...

    def create_hold(self, command: ExperienceHoldCommand) -> ExperienceHold: ...

    def create_booking(self, command: ExperienceBookingCommand) -> ExperienceBooking: ...

    def get_booking(self, supplier_reference: str) -> ExperienceBooking: ...

    def get_voucher(self, supplier_reference: str) -> bytes: ...

    def quote_cancellation(
        self, supplier_reference: str
    ) -> ExperienceCancellationQuote: ...

    def cancel_booking(
        self, command: ExperienceCancellationCommand
    ) -> ExperienceCancellation: ...
