"""
DuffelFlightProvider — build_request/parse_response mapping, Duffel-specific
error translation, and health checks. Every response body here is shaped
per Duffel's public API documentation (https://duffel.com/docs/api/offer-requests)
so the mapping logic is tested against a structurally accurate payload —
it is not real airline inventory and no live network call is made
anywhere in this file (FakeTransport only, per docs/LIVE_PROVIDER_ADAPTER_GUIDE.md).
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
from travelos.live_providers.adapters.duffel_flight_provider import DuffelFlightProvider
from travelos.live_providers.transport import FakeTransport

_ENV_VAR = "DUFFEL_API_TOKEN"

# A direct (0-stop) offer and a 1-stop offer, both shaped exactly as
# Duffel's documented offer_requests response — recorded/hand-built from
# the public API docs, not captured from a real account.
_DIRECT_OFFER = {
    "id": "off_0000A3xLU6b1Xf3JzeVIsQ",
    "total_amount": "246.24",
    "total_currency": "GBP",
    "owner": {"name": "British Airways", "iata_code": "BA"},
    "slices": [
        {
            "duration": "PT8H30M",
            "segments": [
                {
                    "origin": {"iata_code": "LHR"},
                    "destination": {"iata_code": "JFK"},
                    "departing_at": "2026-10-01T14:00:00",
                    "arriving_at": "2026-10-01T22:30:00",
                    "marketing_carrier": {"iata_code": "BA", "name": "British Airways"},
                    "marketing_carrier_flight_number": "117",
                    "passengers": [
                        {"cabin_class": "economy", "baggages": [{"type": "checked", "quantity": 1}]}
                    ],
                }
            ],
        }
    ],
    "conditions": {
        "refund_before_departure": {"allowed": False},
        "change_before_departure": {"allowed": True, "penalty_amount": "50.00"},
    },
}

_ONE_STOP_OFFER = {
    "id": "off_0000A3xLU6b1Xf3JzeVIsR",
    "total_amount": "189.50",
    "total_currency": "GBP",
    "owner": {"name": "Iberia", "iata_code": "IB"},
    "slices": [
        {
            "duration": "PT11H45M",
            "segments": [
                {
                    "origin": {"iata_code": "LHR"},
                    "destination": {"iata_code": "MAD"},
                    "departing_at": "2026-10-01T09:00:00",
                    "arriving_at": "2026-10-01T12:15:00",
                    "marketing_carrier": {"iata_code": "IB", "name": "Iberia"},
                    "marketing_carrier_flight_number": "3166",
                    "passengers": [{"cabin_class": "economy", "baggages": []}],
                },
                {
                    "origin": {"iata_code": "MAD"},
                    "destination": {"iata_code": "JFK"},
                    "departing_at": "2026-10-01T14:00:00",
                    "arriving_at": "2026-10-01T20:45:00",
                    "marketing_carrier": {"iata_code": "IB", "name": "Iberia"},
                    "marketing_carrier_flight_number": "6252",
                    "passengers": [{"cabin_class": "economy", "baggages": []}],
                },
            ],
        }
    ],
    "conditions": {
        "refund_before_departure": {"allowed": False},
        "change_before_departure": {"allowed": False},
    },
}


def _offer_request_body(*offers: dict) -> dict:
    return {"data": {"id": "orq_0000AWpXxOR3AXaXpVAZQP", "offers": list(offers)}}


def _duffel_error_body(error_type: str, code: str = "", message: str = "boom") -> dict:
    return {"errors": [{"type": error_type, "code": code, "message": message}]}


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv(_ENV_VAR, raising=False)


def _req(**params) -> ProviderRequest:
    return ProviderRequest(
        capability=Capability.FLIGHTS,
        operation="search",
        params={
            "origin": "LHR",
            "destination": "JFK",
            "departure_date": "2026-10-01",
            "return_date": None,
            "cabin_class": "economy",
            **params,
        },
    )


class TestRequestMapping:
    def test_build_request_maps_one_way_search(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport.always_returning(status_code=200, body=_offer_request_body(_DIRECT_OFFER))
        provider = DuffelFlightProvider(transport=transport)
        provider.execute(_req())

        sent = transport.sent_requests[0]
        assert sent.method == "POST"
        assert sent.url == "https://api.duffel.com/air/offer_requests?return_offers=true"
        assert sent.headers["Duffel-Version"] == "v2"
        assert sent.json_body["data"]["slices"] == [
            {"origin": "LHR", "destination": "JFK", "departure_date": "2026-10-01"}
        ]
        assert sent.json_body["data"]["passengers"] == [{"type": "adult"}]
        assert sent.json_body["data"]["cabin_class"] == "economy"

    def test_build_request_adds_return_slice_for_round_trip(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport.always_returning(status_code=200, body=_offer_request_body(_DIRECT_OFFER))
        provider = DuffelFlightProvider(transport=transport)
        provider.execute(_req(return_date="2026-10-08"))

        sent = transport.sent_requests[0]
        assert sent.json_body["data"]["slices"] == [
            {"origin": "LHR", "destination": "JFK", "departure_date": "2026-10-01"},
            {"origin": "JFK", "destination": "LHR", "departure_date": "2026-10-08"},
        ]

    def test_auth_header_merged_as_bearer_token(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_my-secret-token")
        transport = FakeTransport.always_returning(status_code=200, body=_offer_request_body(_DIRECT_OFFER))
        provider = DuffelFlightProvider(transport=transport)
        provider.execute(_req())
        assert transport.sent_requests[0].headers["Authorization"] == "Bearer duffel_test_my-secret-token"

    def test_no_auth_header_baked_into_build_request_itself(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        provider = DuffelFlightProvider(transport=FakeTransport())
        transport_request = provider.build_request(_req())
        assert "Authorization" not in transport_request.headers


class TestResponseMapping:
    def test_direct_offer_maps_to_the_internal_flight_option_shape(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport.always_returning(status_code=200, body=_offer_request_body(_DIRECT_OFFER))
        provider = DuffelFlightProvider(transport=transport)
        result = provider.execute(_req())

        assert result.status == ProviderStatus.AVAILABLE
        option = result.data[0]
        assert option["airline"] == "British Airways"
        assert option["flight_number"] == "BA117"
        assert option["cabin_class"] == "economy"
        assert option["stops"] == 0
        assert option["layover_duration"] == ""
        assert option["departure_time"] == "14:00"
        assert option["arrival_time"] == "22:30"
        assert option["total_duration"] == "8h 30m"
        assert option["estimated_price"] == 246.24
        assert option["currency"] == "GBP"
        assert option["baggage_included"] is True
        assert option["refundability"] == "non_refundable"
        assert option["flexibility"] == "flexible"
        assert option["departure_date"] == "2026-10-01"
        assert option["_total_duration_minutes"] == 510
        assert option["_layover_minutes"] == 0

    def test_one_stop_offer_computes_stops_and_layover(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport.always_returning(status_code=200, body=_offer_request_body(_ONE_STOP_OFFER))
        provider = DuffelFlightProvider(transport=transport)
        result = provider.execute(_req())

        option = result.data[0]
        assert option["stops"] == 1
        # MAD arrival 12:15 -> MAD departure 14:00 = 105 minutes.
        assert option["_layover_minutes"] == 105
        assert option["layover_duration"] == "1h 45m"
        assert option["baggage_included"] is False
        assert option["refundability"] == "non_refundable"
        assert option["flexibility"] == "fixed"

    def test_provider_offer_id_is_preserved_internally(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport.always_returning(status_code=200, body=_offer_request_body(_DIRECT_OFFER))
        provider = DuffelFlightProvider(transport=transport)
        result = provider.execute(_req())
        assert result.data[0]["_provider_offer_id"] == _DIRECT_OFFER["id"]

    def test_partial_mapping_failure_skips_the_bad_offer_and_keeps_the_rest(self, monkeypatch):
        """T-038's 'partial mapping failure' requirement — one malformed
        offer among several good ones must not discard the whole batch."""
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        broken_offer = {"id": "off_broken", "total_amount": "100.00", "total_currency": "GBP"}  # no slices
        transport = FakeTransport.always_returning(
            status_code=200, body=_offer_request_body(_DIRECT_OFFER, broken_offer, _ONE_STOP_OFFER)
        )
        provider = DuffelFlightProvider(transport=transport)
        result = provider.execute(_req())

        assert result.status == ProviderStatus.AVAILABLE
        assert len(result.data) == 2
        assert {o["airline"] for o in result.data} == {"British Airways", "Iberia"}
        assert result.warnings == ["1 of 3 offer(s) failed to map and were skipped"]
        assert result.source_metadata["raw_offer_count"] == 3
        assert result.source_metadata["mapped_offer_count"] == 2

    def test_every_offer_failing_to_map_still_raises(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        broken_offer = {"id": "off_broken", "total_amount": "100.00", "total_currency": "GBP"}
        transport = FakeTransport.always_returning(status_code=200, body=_offer_request_body(broken_offer))
        provider = DuffelFlightProvider(transport=transport)
        with pytest.raises(ProviderResponseError):
            provider.execute(_req())

    def test_duration_spanning_more_than_a_day_is_parsed(self, monkeypatch):
        """Confirmed against a real Duffel SANDBOX response during T-037's
        live verification (docs/FIRST_LIVE_PROVIDER.md) — a long
        connection can push total duration past 24 hours, and Duffel
        then includes a day component ("P1DT5H15M") this adapter's
        original ISO 8601 parser (built from documentation examples
        only, which never showed a day component) didn't handle."""
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        long_offer = {**_DIRECT_OFFER, "slices": [{**_DIRECT_OFFER["slices"][0], "duration": "P1DT5H15M"}]}
        transport = FakeTransport.always_returning(status_code=200, body=_offer_request_body(long_offer))
        provider = DuffelFlightProvider(transport=transport)
        result = provider.execute(_req())

        option = result.data[0]
        assert option["_total_duration_minutes"] == 24 * 60 + 5 * 60 + 15
        assert option["total_duration"] == "29h 15m"

    def test_every_option_reaches_the_flight_scorer_without_error(self, monkeypatch):
        """The real contract this adapter must satisfy: its output can be
        scored exactly like MockFlightProvider output, with no adapter-
        specific field ever required by ai/discovery/flights/*."""
        from ai.discovery.flights.flight_reasoner import flight_reasoner
        from ai.discovery.flights.flight_risk_assessor import flight_risk_assessor
        from ai.discovery.flights.flight_scorer import flight_scorer

        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport.always_returning(
            status_code=200, body=_offer_request_body(_DIRECT_OFFER, _ONE_STOP_OFFER)
        )
        provider = DuffelFlightProvider(transport=transport)
        result = provider.execute(_req())

        preferences = {
            "cabin_class": "economy", "max_price_usd": 900, "preferred_airlines": [],
            "layover_tolerance": "moderate", "needs_baggage": True, "preferred_departure": "any",
        }
        for option in result.data:
            score_result = flight_scorer.score(option, preferences, trip_duration_days=7)
            assert 0.0 <= score_result["match_score"] <= 1.0
            explanation = flight_reasoner.explain(option, score_result, preferences)
            assert option["airline"] in explanation
            risks = flight_risk_assessor.assess(option)
            assert isinstance(risks, list)

    def test_source_metadata_carries_the_duffel_request_id(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport.always_returning(status_code=200, body=_offer_request_body(_DIRECT_OFFER))
        provider = DuffelFlightProvider(transport=transport)
        result = provider.execute(_req())
        assert result.source_metadata["provider_request_id"] == "orq_0000AWpXxOR3AXaXpVAZQP"

    def test_missing_data_key_raises_response_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport.always_returning(status_code=200, body={"unexpected": "shape"})
        provider = DuffelFlightProvider(transport=transport)
        with pytest.raises(ProviderResponseError):
            provider.execute(_req())

    def test_offers_not_a_list_raises_response_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport.always_returning(status_code=200, body={"data": {"id": "x", "offers": "nope"}})
        provider = DuffelFlightProvider(transport=transport)
        with pytest.raises(ProviderResponseError):
            provider.execute(_req())

    def test_offer_missing_a_required_field_raises_response_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        broken_offer = {"id": "off_broken", "total_amount": "100.00", "total_currency": "GBP"}  # no slices
        transport = FakeTransport.always_returning(status_code=200, body=_offer_request_body(broken_offer))
        provider = DuffelFlightProvider(transport=transport)
        with pytest.raises(ProviderResponseError):
            provider.execute(_req())

    def test_non_dict_body_raises_response_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport.always_returning(status_code=200, body="not a dict")
        provider = DuffelFlightProvider(transport=transport)
        with pytest.raises(ProviderResponseError):
            provider.execute(_req())


class TestSecretAbsence:
    def test_execute_raises_configuration_error_when_token_unset(self):
        provider = DuffelFlightProvider(transport=FakeTransport())
        with pytest.raises(ProviderConfigurationError):
            provider.execute(_req())

    def test_transport_never_called_when_token_unset(self):
        transport = FakeTransport()
        provider = DuffelFlightProvider(transport=transport)
        with pytest.raises(ProviderConfigurationError):
            provider.execute(_req())
        assert transport.sent_requests == []


class TestStandardErrorMapping:
    """HTTP-status-only failures — BaseLiveProvider's default mapping,
    unchanged by this adapter."""

    def test_401_maps_to_authentication_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport.always_returning(status_code=401, body=_duffel_error_body("authentication_error"))
        provider = DuffelFlightProvider(transport=transport)
        with pytest.raises(ProviderAuthenticationError):
            provider.execute(_req())

    def test_408_maps_to_timeout_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport.always_returning(status_code=408)
        provider = DuffelFlightProvider(transport=transport)
        with pytest.raises(ProviderTimeoutError):
            provider.execute(_req())

    def test_429_maps_to_rate_limit_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport.always_returning(status_code=429, body=_duffel_error_body("rate_limit_error"))
        provider = DuffelFlightProvider(transport=transport)
        with pytest.raises(ProviderRateLimitError):
            provider.execute(_req())

    def test_500_maps_to_unavailable_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport.always_returning(status_code=500)
        provider = DuffelFlightProvider(transport=transport)
        with pytest.raises(ProviderUnavailableError):
            provider.execute(_req())

    def test_503_maps_to_unavailable_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport.always_returning(status_code=503)
        provider = DuffelFlightProvider(transport=transport)
        with pytest.raises(ProviderUnavailableError):
            provider.execute(_req())


class TestDuffelErrorBodyTranslation:
    """422 validation errors don't map to a specific type by HTTP status
    alone (BaseLiveProvider's _check_response_status only recognises
    401/403/408/429/5xx) — map_error() inspects Duffel's structured error
    body to classify them correctly as non-retryable ProviderValidationError."""

    def test_422_validation_error_is_reclassified_as_validation_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport.always_returning(
            status_code=422,
            body=_duffel_error_body("validation_error", code="invalid_slice", message="origin airport not found"),
        )
        provider = DuffelFlightProvider(transport=transport)
        with pytest.raises(ProviderValidationError, match="invalid_slice"):
            provider.execute(_req())

    def test_422_without_a_recognised_error_type_falls_back_to_response_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport.always_returning(status_code=422, body={"errors": [{"type": "something_new"}]})
        provider = DuffelFlightProvider(transport=transport)
        with pytest.raises(ProviderResponseError):
            provider.execute(_req())

    def test_validation_error_is_never_retried(self, monkeypatch):
        """ProviderValidationError is in RetryPolicy._NEVER_RETRYABLE —
        confirms the reclassification actually changes gateway behaviour,
        not just the exception's name."""
        from travelos.intelligence_gateway.retry_policy import RetryPolicy

        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        transport = FakeTransport.always_returning(
            status_code=422, body=_duffel_error_body("validation_error", code="invalid_slice"),
        )
        provider = DuffelFlightProvider(transport=transport)
        try:
            provider.execute(_req())
        except ProviderValidationError as exc:
            assert not RetryPolicy().is_retryable(exc)
        else:
            pytest.fail("expected ProviderValidationError")


class TestHealthChecks:
    def test_unconfigured_provider_is_misconfigured(self):
        provider = DuffelFlightProvider(transport=FakeTransport())
        assert provider.health_check() == ProviderStatus.MISCONFIGURED

    def test_configured_provider_is_available(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        provider = DuffelFlightProvider(transport=FakeTransport())
        assert provider.health_check() == ProviderStatus.AVAILABLE

    def test_detailed_health_never_includes_the_token_value(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "super-secret-should-not-appear")
        provider = DuffelFlightProvider(transport=FakeTransport())
        detailed = provider.health_check_detailed()
        assert "super-secret-should-not-appear" not in str(detailed)

    def test_environment_defaults_to_sandbox(self):
        provider = DuffelFlightProvider(transport=FakeTransport())
        assert provider.environment == ProviderEnvironment.SANDBOX

    def test_mock_environment_is_rejected(self):
        with pytest.raises(ValueError):
            DuffelFlightProvider(transport=FakeTransport(), environment=ProviderEnvironment.MOCK)


class TestUnsupportedOperation:
    def test_non_search_operation_raises_validation_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        provider = DuffelFlightProvider(transport=FakeTransport())
        bad_request = ProviderRequest(capability=Capability.FLIGHTS, operation="book", params={})
        with pytest.raises(ProviderValidationError):
            provider.execute(bad_request)
