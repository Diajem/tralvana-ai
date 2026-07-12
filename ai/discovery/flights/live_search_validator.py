"""
Pre-flight validation for a live Duffel sandbox search (T-038, section 3)
— every check here runs before any provider call, so an invalid request
never reaches Duffel. Deliberately scoped to LIVE_SANDBOX mode only
(services/api/app/domains/flights/service.py gates the call on
`config.flight_provider_mode`): MockFlightProvider has never required
IATA codes (its own tests and existing callers freely use city names
like "London"), and MOCK mode's public API behaviour must stay
byte-identical to before T-038 — validation only starts mattering the
moment a real vendor call could actually happen.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone

_IATA_RE = re.compile(r"^[A-Z]{3}$")
_VALID_CABIN_CLASSES = ("economy", "business", "first")
_MIN_ADULTS = 1
_MAX_ADULTS = 9


class LiveFlightSearchValidationError(ValueError):
    """Carries every validation problem found, not just the first —
    services/api/app/domains/flights/router.py renders `errors` as the
    422 response detail."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


def validate_live_flight_search(
    origin: str,
    destination: str,
    departure_date: str | None,
    return_date: str | None,
    adults: int,
    cabin_class: str,
) -> None:
    errors: list[str] = []

    origin_iata = (origin or "").strip().upper()
    destination_iata = (destination or "").strip().upper()

    if not _IATA_RE.match(origin_iata):
        errors.append(f"origin must be a 3-letter IATA airport code, got {origin!r}")
    if not _IATA_RE.match(destination_iata):
        errors.append(f"destination must be a 3-letter IATA airport code, got {destination!r}")
    if origin_iata and destination_iata and origin_iata == destination_iata:
        errors.append("origin and destination must differ")

    departure = _parse_date(departure_date, "departure_date", required=True, errors=errors)
    returning = _parse_date(return_date, "return_date", required=False, errors=errors)

    today = datetime.now(timezone.utc).date()
    if departure is not None and departure < today:
        errors.append("departure_date must not be in the past")
    if returning is not None and departure is not None and returning <= departure:
        errors.append("return_date must be after departure_date")

    if not (_MIN_ADULTS <= adults <= _MAX_ADULTS):
        errors.append(f"adults must be between {_MIN_ADULTS} and {_MAX_ADULTS}, got {adults}")

    if cabin_class not in _VALID_CABIN_CLASSES:
        errors.append(f"cabin_class must be one of {list(_VALID_CABIN_CLASSES)}, got {cabin_class!r}")

    if errors:
        raise LiveFlightSearchValidationError(errors)


def _parse_date(value: str | None, field_name: str, required: bool, errors: list[str]) -> date | None:
    if not value:
        if required:
            errors.append(f"{field_name} is required for a live sandbox search")
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        errors.append(f"{field_name} must be in YYYY-MM-DD format, got {value!r}")
        return None
