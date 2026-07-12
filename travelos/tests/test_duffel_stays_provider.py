"""
DuffelStaysProvider — destination resolution (Places API), request/
response mapping, Duffel-specific error translation (including the
account-not-enabled 403 confirmed against the real API during T-039),
and health checks. Every response body here is shaped per Duffel's
public API documentation (https://duffel.com/docs/api/v2/search,
https://duffel.com/docs/api/places/get-place-suggestions) — not real
inventory, and no live network call is made anywhere in this file
(FakeTransport only).
"""

from __future__ import annotations

import pytest

from travelos.intelligence_gateway.exceptions import (
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderValidationError,
)
from travelos.intelligence_gateway.provider_contract import ProviderRequest
from travelos.intelligence_gateway.provider_status import Capability, ProviderEnvironment, ProviderStatus
from travelos.live_providers.adapters.duffel_stays_provider import DuffelStaysProvider
from travelos.live_providers.transport import FakeTransport, TransportResponse

_ENV_VAR = "DUFFEL_API_TOKEN"

_PLACES_BODY = {
    "data": [
        {"id": "place_airport", "type": "airport", "name": "Tokyo Haneda", "latitude": 35.5494, "longitude": 139.7798},
        {"id": "place_city", "type": "city", "name": "Tokyo", "latitude": 35.6762, "longitude": 139.6503},
    ]
}

_DIRECT_RESULT = {
    "id": "sr_0000A",
    "rooms": 1,
    "guests": [{"type": "adult"}],
    "check_in_date": "2026-10-01",
    "check_out_date": "2026-10-03",
    "cheapest_rate_total_amount": "240.00",
    "cheapest_rate_currency": "USD",
    "accommodation": {
        "id": "acc_0000A",
        "name": "Duffel Test Hotel Tokyo",
        "rating": 4,
        "review_score": 8.7,
        "review_count": 340,
        "amenities": ["pool", "wheelchair_accessible", "workspace"],
        "location": {
            "geographic_coordinates": {"latitude": 35.68, "longitude": 139.65},
            "address": {"line_one": "1 Test Street", "city_name": "Tokyo", "region": "Tokyo", "country_code": "JP"},
        },
        "rooms": [
            {
                "name": "Standard Room",
                "rates": [
                    {
                        "id": "rate_0000A",
                        "total_amount": "240.00",
                        "total_currency": "USD",
                        "board_type": "breakfast",
                        "cancellation_timeline": [
                            {"refund_amount": "240.00", "currency": "USD", "before": "2026-09-25T00:00:00Z"}
                        ],
                    }
                ],
            }
        ],
    },
}

_SEARCH_ONLY_RESULT = {
    # No rooms/rates — per Duffel's own docs, "a search result's
    # accommodation may not include rooms and rates information...
    # but you will always know the price of the cheapest rate".
    "id": "sr_0000B",
    "cheapest_rate_total_amount": "95.00",
    "cheapest_rate_currency": "USD",
    "accommodation": {
        "id": "acc_0000B",
        "name": "Budget Test Inn",
        "location": {
            "geographic_coordinates": {"latitude": 35.70, "longitude": 139.70},
            "address": {"city_name": "Tokyo"},
        },
    },
}


def _places_and_search_responder(search_status=200, search_body=None):
    def responder(request):
        if "places/suggestions" in request.url:
            return TransportResponse(status_code=200, body=_PLACES_BODY)
        return TransportResponse(status_code=search_status, body=search_body)
    return responder


def _search_body(*results: dict) -> dict:
    return {"data": {"created_at": "2026-07-13T00:00:00Z", "results": list(results)}}


def _duffel_error_body(error_type: str, code: str = "", message: str = "boom") -> dict:
    return {"errors": [{"type": error_type, "code": code, "message": message}]}


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv(_ENV_VAR, raising=False)


def _req(**params) -> ProviderRequest:
    return ProviderRequest(
        capability=Capability.ACCOMMODATION,
        operation="search",
        params={
            "destination": "Tokyo", "check_in_date": "2026-10-01", "nights": 2,
            "adults": 1, "children": 0, "rooms": 1,
            **params,
        },
    )


class TestDestinationResolution:
    def test_resolves_via_places_api_preferring_city_type(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport(responder=_places_and_search_responder(search_body=_search_body(_DIRECT_RESULT)))
        provider = DuffelStaysProvider(transport=transport)
        provider.execute(_req())

        places_request = transport.sent_requests[0]
        assert places_request.method == "GET"
        assert "places/suggestions" in places_request.url
        assert places_request.query_params["query"] == "Tokyo"

        search_request = transport.sent_requests[1]
        location = search_request.json_body["location"]["geographic_coordinates"]
        # City coordinates (35.6762), not the airport's (35.5494).
        assert location["latitude"] == 35.6762
        assert location["longitude"] == 139.6503

    def test_falls_back_to_first_place_when_no_city_type(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")

        def responder(request):
            if "places/suggestions" in request.url:
                return TransportResponse(status_code=200, body={"data": [_PLACES_BODY["data"][0]]})
            return TransportResponse(status_code=200, body=_search_body(_DIRECT_RESULT))

        transport = FakeTransport(responder=responder)
        provider = DuffelStaysProvider(transport=transport)
        provider.execute(_req())
        location = transport.sent_requests[1].json_body["location"]["geographic_coordinates"]
        assert location["latitude"] == 35.5494

    def test_city_place_missing_coordinates_falls_back_to_a_geocoded_airport(self, monkeypatch):
        """Confirmed against the real Duffel API during T-039's live
        verification: querying "Tokyo" returns a city place with
        latitude/longitude both null, alongside airport places that do
        carry coordinates. The original assumption (first city match
        wins unconditionally) failed against this exact real response —
        fixed to prefer the first *geocoded* place, city type first."""
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        ungeocoded_city = {"id": "place_city", "type": "city", "name": "Tokyo", "latitude": None, "longitude": None}
        geocoded_airport = {"id": "place_airport", "type": "airport", "name": "Haneda", "latitude": 35.5494, "longitude": 139.7798}

        def responder(request):
            if "places/suggestions" in request.url:
                return TransportResponse(status_code=200, body={"data": [ungeocoded_city, geocoded_airport]})
            return TransportResponse(status_code=200, body=_search_body(_DIRECT_RESULT))

        transport = FakeTransport(responder=responder)
        provider = DuffelStaysProvider(transport=transport)
        provider.execute(_req())
        location = transport.sent_requests[1].json_body["location"]["geographic_coordinates"]
        assert location["latitude"] == 35.5494
        assert location["longitude"] == 139.7798

    def test_no_geocoded_place_at_all_raises_validation_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        ungeocoded_city = {"id": "place_city", "type": "city", "name": "Nowhere", "latitude": None, "longitude": None}

        def responder(request):
            if "places/suggestions" in request.url:
                return TransportResponse(status_code=200, body={"data": [ungeocoded_city]})
            return TransportResponse(status_code=200, body=_search_body(_DIRECT_RESULT))

        transport = FakeTransport(responder=responder)
        provider = DuffelStaysProvider(transport=transport)
        with pytest.raises(ProviderValidationError):
            provider.execute(_req(destination="Nowhere"))

    def test_no_matching_place_raises_validation_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")

        def responder(request):
            return TransportResponse(status_code=200, body={"data": []})

        transport = FakeTransport(responder=responder)
        provider = DuffelStaysProvider(transport=transport)
        with pytest.raises(ProviderValidationError):
            provider.execute(_req(destination="Nowhereville"))

    def test_places_lookup_never_leaks_into_request_headers_incorrectly(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_my-secret-token")
        transport = FakeTransport(responder=_places_and_search_responder(search_body=_search_body(_DIRECT_RESULT)))
        provider = DuffelStaysProvider(transport=transport)
        provider.execute(_req())
        for sent in transport.sent_requests:
            assert sent.headers.get("Authorization") == "Bearer duffel_test_my-secret-token"


class TestRequestMapping:
    def test_check_out_date_computed_from_nights(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport(responder=_places_and_search_responder(search_body=_search_body(_DIRECT_RESULT)))
        provider = DuffelStaysProvider(transport=transport)
        provider.execute(_req(check_in_date="2026-10-01", nights=3))
        body = transport.sent_requests[1].json_body
        assert body["check_in_date"] == "2026-10-01"
        assert body["check_out_date"] == "2026-10-04"

    def test_guests_and_rooms_mapped(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport(responder=_places_and_search_responder(search_body=_search_body(_DIRECT_RESULT)))
        provider = DuffelStaysProvider(transport=transport)
        provider.execute(_req(adults=2, children=1, rooms=2))
        body = transport.sent_requests[1].json_body
        assert body["rooms"] == 2
        assert body["guests"] == [{"type": "adult"}, {"type": "adult"}, {"type": "child"}]

    def test_radius_included_and_configurable(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport(responder=_places_and_search_responder(search_body=_search_body(_DIRECT_RESULT)))
        provider = DuffelStaysProvider(transport=transport, search_radius_km=25.0)
        provider.execute(_req())
        body = transport.sent_requests[1].json_body
        assert body["location"]["radius"] == 25.0

    def test_search_request_has_no_auth_header_of_its_own(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport(responder=_places_and_search_responder(search_body=_search_body(_DIRECT_RESULT)))
        provider = DuffelStaysProvider(transport=transport)
        transport_request = provider.build_request(_req())
        assert "Authorization" not in transport_request.headers


class TestResponseMapping:
    def test_full_result_maps_to_raw_duffel_shape(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport(responder=_places_and_search_responder(search_body=_search_body(_DIRECT_RESULT)))
        provider = DuffelStaysProvider(transport=transport)
        result = provider.execute(_req())

        assert result.status == ProviderStatus.AVAILABLE
        raw = result.data[0]
        assert raw["_provider_source"] == "duffel_stays"
        assert raw["_provider_property_id"] == "acc_0000A"
        assert raw["_provider_rate_id"] == "rate_0000A"
        assert raw["property_name"] == "Duffel Test Hotel Tokyo"
        assert raw["duffel_rating"] == 4
        assert raw["duffel_review_score"] == 8.7
        assert raw["duffel_amenities"] == ["pool", "wheelchair_accessible", "workspace"]
        assert raw["duffel_latitude"] == 35.68
        assert raw["duffel_longitude"] == 139.65
        assert raw["duffel_city_name"] == "Tokyo"
        assert raw["board_type"] == "breakfast"
        assert raw["total_price"] == 240.0
        assert raw["nightly_price"] == 120.0
        assert raw["currency"] == "USD"
        assert raw["nights"] == 2
        assert raw["check_in_date"] == "2026-10-01"
        assert raw["search_latitude"] == 35.6762
        assert raw["search_longitude"] == 139.6503

    def test_search_only_result_falls_back_to_cheapest_rate_fields(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport(responder=_places_and_search_responder(search_body=_search_body(_SEARCH_ONLY_RESULT)))
        provider = DuffelStaysProvider(transport=transport)
        result = provider.execute(_req())

        raw = result.data[0]
        assert raw["_provider_property_id"] == "acc_0000B"
        assert raw["_provider_rate_id"] == "sr_0000B"  # falls back to the search result's own id
        assert raw["total_price"] == 95.0
        assert raw["board_type"] is None
        assert raw["cancellation_timeline"] is None

    def test_multiple_results_all_mapped(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport(
            responder=_places_and_search_responder(search_body=_search_body(_DIRECT_RESULT, _SEARCH_ONLY_RESULT))
        )
        provider = DuffelStaysProvider(transport=transport)
        result = provider.execute(_req())
        assert len(result.data) == 2
        assert result.source_metadata["raw_result_count"] == 2
        assert result.source_metadata["mapped_result_count"] == 2

    def test_partial_mapping_failure_skips_bad_result_keeps_rest(self, monkeypatch):
        broken_result = {"id": "sr_broken", "accommodation": {"id": "acc_broken"}}  # no name, no price anywhere
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport(
            responder=_places_and_search_responder(
                search_body=_search_body(_DIRECT_RESULT, broken_result, _SEARCH_ONLY_RESULT)
            )
        )
        provider = DuffelStaysProvider(transport=transport)
        result = provider.execute(_req())

        assert result.status == ProviderStatus.AVAILABLE
        assert len(result.data) == 2
        assert result.warnings == ["1 of 3 search result(s) failed to map and were skipped"]
        assert result.source_metadata["raw_result_count"] == 3
        assert result.source_metadata["mapped_result_count"] == 2

    def test_every_result_failing_to_map_raises(self, monkeypatch):
        broken_result = {"id": "sr_broken", "accommodation": {"id": "acc_broken"}}
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport(responder=_places_and_search_responder(search_body=_search_body(broken_result)))
        provider = DuffelStaysProvider(transport=transport)
        with pytest.raises(ProviderResponseError):
            provider.execute(_req())

    def test_zero_results_is_not_an_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport(responder=_places_and_search_responder(search_body=_search_body()))
        provider = DuffelStaysProvider(transport=transport)
        result = provider.execute(_req())
        assert result.status == ProviderStatus.AVAILABLE
        assert result.data == []

    def test_missing_data_key_raises_response_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport(responder=_places_and_search_responder(search_body={"unexpected": "shape"}))
        provider = DuffelStaysProvider(transport=transport)
        with pytest.raises(ProviderResponseError):
            provider.execute(_req())

    def test_non_dict_body_raises_response_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport(responder=_places_and_search_responder(search_body="not a dict"))
        provider = DuffelStaysProvider(transport=transport)
        with pytest.raises(ProviderResponseError):
            provider.execute(_req())


class TestSecretAbsence:
    def test_execute_raises_configuration_error_when_token_unset(self):
        provider = DuffelStaysProvider(transport=FakeTransport())
        with pytest.raises(ProviderConfigurationError):
            provider.execute(_req())

    def test_no_transport_call_when_token_unset(self):
        transport = FakeTransport()
        provider = DuffelStaysProvider(transport=transport)
        with pytest.raises(ProviderConfigurationError):
            provider.execute(_req())
        assert transport.sent_requests == []


class TestStandardErrorMapping:
    def test_401_maps_to_authentication_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport(responder=_places_and_search_responder(search_status=401))
        provider = DuffelStaysProvider(transport=transport)
        with pytest.raises(ProviderAuthenticationError):
            provider.execute(_req())

    def test_408_maps_to_timeout_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport(responder=_places_and_search_responder(search_status=408))
        provider = DuffelStaysProvider(transport=transport)
        with pytest.raises(ProviderTimeoutError):
            provider.execute(_req())

    def test_429_maps_to_rate_limit_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport(
            responder=_places_and_search_responder(search_status=429, search_body=_duffel_error_body("rate_limit_error"))
        )
        provider = DuffelStaysProvider(transport=transport)
        with pytest.raises(ProviderRateLimitError):
            provider.execute(_req())

    def test_500_maps_to_unavailable_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport(responder=_places_and_search_responder(search_status=500))
        provider = DuffelStaysProvider(transport=transport)
        with pytest.raises(ProviderUnavailableError):
            provider.execute(_req())


class TestAccountNotEnabledForStays:
    """Confirmed against the real Duffel API during T-039: a token
    without Stays access returns a plain-text (not JSON) 403 body —
    "This feature is not enabled for your account." — reproduced here
    exactly as observed, not guessed."""

    def test_plain_text_403_maps_to_a_clear_validation_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")

        def responder(request):
            if "places/suggestions" in request.url:
                return TransportResponse(status_code=200, body=_PLACES_BODY)
            return TransportResponse(
                status_code=403,
                body="This feature is not enabled for your account. Please contact sales to get access: https://duffel.com/contact-us",
            )

        transport = FakeTransport(responder=responder)
        provider = DuffelStaysProvider(transport=transport)
        with pytest.raises(ProviderValidationError, match="not enabled for this account"):
            provider.execute(_req())

    def test_account_not_enabled_error_never_retried(self, monkeypatch):
        from travelos.intelligence_gateway.retry_policy import RetryPolicy

        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")

        def responder(request):
            if "places/suggestions" in request.url:
                return TransportResponse(status_code=200, body=_PLACES_BODY)
            return TransportResponse(status_code=403, body="This feature is not enabled for your account.")

        transport = FakeTransport(responder=responder)
        provider = DuffelStaysProvider(transport=transport)
        try:
            provider.execute(_req())
        except ProviderValidationError as exc:
            assert not RetryPolicy().is_retryable(exc)
        else:
            pytest.fail("expected ProviderValidationError")


class TestDuffelErrorBodyTranslation:
    def test_validation_error_body_reclassified(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport(
            responder=_places_and_search_responder(
                search_status=422, search_body=_duffel_error_body("validation_error", code="invalid_location")
            )
        )
        provider = DuffelStaysProvider(transport=transport)
        with pytest.raises(ProviderValidationError, match="invalid_location"):
            provider.execute(_req())


class TestHealthChecks:
    def test_unconfigured_provider_is_misconfigured(self):
        provider = DuffelStaysProvider(transport=FakeTransport())
        assert provider.health_check() == ProviderStatus.MISCONFIGURED

    def test_configured_provider_is_available(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        provider = DuffelStaysProvider(transport=FakeTransport())
        assert provider.health_check() == ProviderStatus.AVAILABLE

    def test_detailed_health_never_includes_the_token_value(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "super-secret-should-not-appear")
        provider = DuffelStaysProvider(transport=FakeTransport())
        detailed = provider.health_check_detailed()
        assert "super-secret-should-not-appear" not in str(detailed)

    def test_environment_defaults_to_sandbox(self):
        provider = DuffelStaysProvider(transport=FakeTransport())
        assert provider.environment == ProviderEnvironment.SANDBOX

    def test_mock_environment_is_rejected(self):
        with pytest.raises(ValueError):
            DuffelStaysProvider(transport=FakeTransport(), environment=ProviderEnvironment.MOCK)


class TestUnsupportedOperation:
    def test_non_search_operation_raises_validation_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        provider = DuffelStaysProvider(transport=FakeTransport())
        bad_request = ProviderRequest(capability=Capability.ACCOMMODATION, operation="book", params={})
        with pytest.raises(ProviderValidationError):
            provider.execute(bad_request)
