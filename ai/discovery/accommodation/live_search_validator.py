"""
Pre-flight validation for a live Duffel Stays sandbox search (T-039,
section 4) — every check here runs before any provider call, so an
invalid request never reaches Duffel. Deliberately scoped to
LIVE_SANDBOX mode only (services/api/app/domains/accommodation/service.py
gates the call on `config.accommodation_provider_mode`): MockAccommodationProvider
has never validated its inputs this strictly, and MOCK mode's public
API behaviour must stay byte-identical to before T-039.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

_MIN_ADULTS = 1
_MAX_ADULTS = 9
_MIN_ROOMS = 1
_MAX_ROOMS = 8
_MAX_NIGHTS = 99  # Duffel's own documented maximum stay length


class LiveAccommodationSearchValidationError(ValueError):
    """Carries every validation problem found, not just the first —
    services/api/app/domains/accommodation/router.py renders `errors`
    as the 422 response detail."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


def validate_live_accommodation_search(
    destination: str,
    check_in_date: str | None,
    nights: int,
    adults: int,
    rooms: int,
) -> None:
    errors: list[str] = []

    if not (destination or "").strip():
        errors.append("destination is required for a live sandbox search")

    check_in = _parse_date(check_in_date, "check_in_date", required=True, errors=errors)

    today = datetime.now(timezone.utc).date()
    if check_in is not None and check_in < today:
        errors.append("check_in_date must not be in the past")

    if not isinstance(nights, int) or nights < 1:
        errors.append(f"nights must be at least 1, got {nights!r}")
    elif nights > _MAX_NIGHTS:
        errors.append(f"stay length must be at most {_MAX_NIGHTS} nights, got {nights}")

    if not (_MIN_ADULTS <= adults <= _MAX_ADULTS):
        errors.append(f"adults must be between {_MIN_ADULTS} and {_MAX_ADULTS}, got {adults}")

    if not (_MIN_ROOMS <= rooms <= _MAX_ROOMS):
        errors.append(f"rooms must be between {_MIN_ROOMS} and {_MAX_ROOMS}, got {rooms}")

    if errors:
        raise LiveAccommodationSearchValidationError(errors)


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
