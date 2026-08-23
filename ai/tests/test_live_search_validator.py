"""validate_live_flight_search (T-038, section 3) — every rule, run
before any Duffel call is made."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ai.discovery.flights.live_search_validator import (
    LiveFlightSearchValidationError,
    validate_live_flight_search,
)

_TOMORROW = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
_NEXT_WEEK = (datetime.now(timezone.utc) + timedelta(days=8)).strftime("%Y-%m-%d")
_YESTERDAY = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")


def _valid(**overrides) -> dict:
    base = dict(origin="LHR", destination="JFK", departure_date=_TOMORROW, return_date=None, adults=1, cabin_class="economy")
    base.update(overrides)
    return base


class TestValidRequestsPass:
    def test_one_way_valid_request_does_not_raise(self):
        validate_live_flight_search(**_valid())

    def test_round_trip_valid_request_does_not_raise(self):
        validate_live_flight_search(**_valid(return_date=_NEXT_WEEK))

    def test_all_cabin_classes_accepted(self):
        for cabin in ("economy", "business", "first"):
            validate_live_flight_search(**_valid(cabin_class=cabin))

    def test_max_adults_boundary_accepted(self):
        validate_live_flight_search(**_valid(adults=9))

    def test_min_adults_boundary_accepted(self):
        validate_live_flight_search(**_valid(adults=1))


class TestPlaceValidation:
    def test_lowercase_origin_is_normalised_and_accepted(self):
        validate_live_flight_search(**_valid(origin="lhr"))

    def test_city_name_origin_is_accepted_for_private_resolution(self):
        validate_live_flight_search(**_valid(origin="London"))

    def test_city_name_destination_is_accepted_for_private_resolution(self):
        validate_live_flight_search(**_valid(destination="New York"))

    def test_blank_origin_rejected(self):
        with pytest.raises(LiveFlightSearchValidationError):
            validate_live_flight_search(**_valid(origin=""))

    def test_origin_equals_destination_rejected(self):
        with pytest.raises(LiveFlightSearchValidationError) as exc_info:
            validate_live_flight_search(**_valid(origin="LHR", destination="LHR"))
        assert any("differ" in e for e in exc_info.value.errors)


class TestDateValidation:
    def test_missing_departure_date_rejected(self):
        with pytest.raises(LiveFlightSearchValidationError) as exc_info:
            validate_live_flight_search(**_valid(departure_date=None))
        assert any("departure_date" in e for e in exc_info.value.errors)

    def test_departure_date_in_the_past_rejected(self):
        with pytest.raises(LiveFlightSearchValidationError) as exc_info:
            validate_live_flight_search(**_valid(departure_date=_YESTERDAY))
        assert any("past" in e for e in exc_info.value.errors)

    def test_malformed_departure_date_rejected(self):
        with pytest.raises(LiveFlightSearchValidationError):
            validate_live_flight_search(**_valid(departure_date="15-10-2026"))

    def test_return_date_before_departure_rejected(self):
        with pytest.raises(LiveFlightSearchValidationError) as exc_info:
            validate_live_flight_search(**_valid(departure_date=_NEXT_WEEK, return_date=_TOMORROW))
        assert any("after" in e for e in exc_info.value.errors)

    def test_return_date_equal_to_departure_rejected(self):
        with pytest.raises(LiveFlightSearchValidationError):
            validate_live_flight_search(**_valid(departure_date=_TOMORROW, return_date=_TOMORROW))

    def test_malformed_return_date_rejected(self):
        with pytest.raises(LiveFlightSearchValidationError):
            validate_live_flight_search(**_valid(return_date="not-a-date"))


class TestPassengerAndCabinValidation:
    def test_zero_adults_rejected(self):
        with pytest.raises(LiveFlightSearchValidationError):
            validate_live_flight_search(**_valid(adults=0))

    def test_too_many_adults_rejected(self):
        with pytest.raises(LiveFlightSearchValidationError):
            validate_live_flight_search(**_valid(adults=10))

    def test_minor_ages_are_required_for_every_under_18_passenger(self):
        with pytest.raises(LiveFlightSearchValidationError) as exc_info:
            validate_live_flight_search(**_valid(minors=2, minor_ages=[]))
        assert any("one age" in error for error in exc_info.value.errors)

    def test_age_aware_family_search_is_accepted(self):
        validate_live_flight_search(**_valid(adults=2, minors=2, minor_ages=[6, 9]))

    def test_invalid_minor_age_is_rejected(self):
        with pytest.raises(LiveFlightSearchValidationError) as exc_info:
            validate_live_flight_search(**_valid(minors=1, minor_ages=[18]))
        assert any("0 to 17" in error for error in exc_info.value.errors)

    def test_total_party_is_bounded(self):
        with pytest.raises(LiveFlightSearchValidationError) as exc_info:
            validate_live_flight_search(**_valid(adults=8, minors=2, minor_ages=[6, 9]))
        assert any("total passengers" in error for error in exc_info.value.errors)

    def test_invalid_cabin_class_rejected(self):
        with pytest.raises(LiveFlightSearchValidationError) as exc_info:
            validate_live_flight_search(**_valid(cabin_class="premium_economy"))
        assert any("cabin_class" in e for e in exc_info.value.errors)


class TestMultipleErrorsCollected:
    def test_every_problem_is_reported_not_just_the_first(self):
        with pytest.raises(LiveFlightSearchValidationError) as exc_info:
            validate_live_flight_search(
                origin="", destination="", departure_date=_YESTERDAY,
                return_date=None, adults=0, cabin_class="luxury",
            )
        assert len(exc_info.value.errors) >= 4
