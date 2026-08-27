"""Provider-neutral accommodation transaction records.

These objects deliberately contain no HBX-specific field names.  A future
Duffel Stays or other transactional adapter can implement the same contract,
allowing checkout and My Trips to remain supplier-independent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class AccommodationGuest:
    room_id: int
    guest_type: str  # ADULT | CHILD
    given_name: str
    family_name: str
    age: int | None = None


@dataclass(frozen=True)
class AccommodationBookingCommand:
    rate_reference: str
    holder_given_name: str
    holder_family_name: str
    guests: tuple[AccommodationGuest, ...]
    client_reference: str
    customer_approved: bool
    rate_status: str = "BOOKABLE"
    expected_total: float | None = None
    expected_currency: str | None = None
    price_tolerance_percent: float = 0.0
    remark: str = ""


@dataclass(frozen=True)
class AccommodationRateQuote:
    provider_name: str
    rate_reference: str
    status: str
    total: float
    currency: str
    rate_comments: str = ""
    cancellation_policies: tuple[dict[str, Any], ...] = ()
    taxes: tuple[dict[str, Any], ...] = ()
    raw_reference: str = ""


@dataclass(frozen=True)
class AccommodationBooking:
    provider_name: str
    supplier_reference: str
    client_reference: str
    status: str
    total: float
    currency: str
    hotel_name: str = ""
    check_in_date: str = ""
    check_out_date: str = ""
    cancellation_policies: tuple[dict[str, Any], ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class AccommodationCancellation:
    provider_name: str
    supplier_reference: str
    status: str
    simulated: bool
    cancellation_amount: float | None = None
    currency: str | None = None
    warnings: tuple[str, ...] = ()


class AccommodationBookingProvider(Protocol):
    def check_rate(self, rate_reference: str) -> AccommodationRateQuote: ...

    def create_booking(self, command: AccommodationBookingCommand) -> AccommodationBooking: ...

    def get_booking(self, supplier_reference: str) -> AccommodationBooking: ...

    def cancel_booking(
        self, supplier_reference: str, *, simulate: bool = True, customer_approved: bool = False
    ) -> AccommodationCancellation: ...
