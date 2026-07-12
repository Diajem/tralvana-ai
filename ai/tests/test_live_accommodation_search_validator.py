"""validate_live_accommodation_search (T-039, section 4) — every rule,
run before any Duffel Stays call is made."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ai.discovery.accommodation.live_search_validator import (
    LiveAccommodationSearchValidationError,
    validate_live_accommodation_search,
)

_TOMORROW = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
_YESTERDAY = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")


def _valid(**overrides) -> dict:
    base = dict(destination="Tokyo", check_in_date=_TOMORROW, nights=3, adults=1, rooms=1)
    base.update(overrides)
    return base


class TestValidRequestsPass:
    def test_valid_request_does_not_raise(self):
        validate_live_accommodation_search(**_valid())

    def test_max_adults_boundary_accepted(self):
        validate_live_accommodation_search(**_valid(adults=9))

    def test_max_rooms_boundary_accepted(self):
        validate_live_accommodation_search(**_valid(rooms=8))

    def test_max_nights_boundary_accepted(self):
        validate_live_accommodation_search(**_valid(nights=99))


class TestDestinationValidation:
    def test_empty_destination_rejected(self):
        with pytest.raises(LiveAccommodationSearchValidationError) as exc_info:
            validate_live_accommodation_search(**_valid(destination=""))
        assert any("destination" in e for e in exc_info.value.errors)

    def test_whitespace_only_destination_rejected(self):
        with pytest.raises(LiveAccommodationSearchValidationError):
            validate_live_accommodation_search(**_valid(destination="   "))


class TestDateValidation:
    def test_missing_check_in_date_rejected(self):
        with pytest.raises(LiveAccommodationSearchValidationError) as exc_info:
            validate_live_accommodation_search(**_valid(check_in_date=None))
        assert any("check_in_date" in e for e in exc_info.value.errors)

    def test_check_in_date_in_the_past_rejected(self):
        with pytest.raises(LiveAccommodationSearchValidationError) as exc_info:
            validate_live_accommodation_search(**_valid(check_in_date=_YESTERDAY))
        assert any("past" in e for e in exc_info.value.errors)

    def test_malformed_check_in_date_rejected(self):
        with pytest.raises(LiveAccommodationSearchValidationError):
            validate_live_accommodation_search(**_valid(check_in_date="01-10-2026"))


class TestStayLengthValidation:
    def test_zero_nights_rejected(self):
        with pytest.raises(LiveAccommodationSearchValidationError):
            validate_live_accommodation_search(**_valid(nights=0))

    def test_too_many_nights_rejected(self):
        with pytest.raises(LiveAccommodationSearchValidationError) as exc_info:
            validate_live_accommodation_search(**_valid(nights=100))
        assert any("99" in e for e in exc_info.value.errors)


class TestGuestAndRoomValidation:
    def test_zero_adults_rejected(self):
        with pytest.raises(LiveAccommodationSearchValidationError):
            validate_live_accommodation_search(**_valid(adults=0))

    def test_too_many_adults_rejected(self):
        with pytest.raises(LiveAccommodationSearchValidationError):
            validate_live_accommodation_search(**_valid(adults=10))

    def test_zero_rooms_rejected(self):
        with pytest.raises(LiveAccommodationSearchValidationError):
            validate_live_accommodation_search(**_valid(rooms=0))

    def test_too_many_rooms_rejected(self):
        with pytest.raises(LiveAccommodationSearchValidationError):
            validate_live_accommodation_search(**_valid(rooms=9))


class TestMultipleErrorsCollected:
    def test_every_problem_is_reported_not_just_the_first(self):
        with pytest.raises(LiveAccommodationSearchValidationError) as exc_info:
            validate_live_accommodation_search(
                destination="", check_in_date=_YESTERDAY, nights=0, adults=0, rooms=0,
            )
        assert len(exc_info.value.errors) >= 4
