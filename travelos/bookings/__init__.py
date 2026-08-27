"""Provider-neutral booking contracts used by transactional suppliers."""

from travelos.bookings.accommodation import (
    AccommodationBooking,
    AccommodationBookingCommand,
    AccommodationCancellation,
    AccommodationGuest,
    AccommodationRateQuote,
)

__all__ = [
    "AccommodationBooking",
    "AccommodationBookingCommand",
    "AccommodationCancellation",
    "AccommodationGuest",
    "AccommodationRateQuote",
]
