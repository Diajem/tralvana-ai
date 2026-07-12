"""
Public /accommodation/recommend behaviour for T-039: response-shape
backward compatibility, LIVE_SANDBOX validation (422) before any
provider call, LIVE_SANDBOX end-to-end through a FakeTransport-backed
Duffel Stays provider, failure/fallback behaviour (503 by default, mock
fallback when enabled), and no secret leakage anywhere in the response.

Live-mode tests swap accommodation_intelligence's `_provider` for the
duration of one test via `monkeypatch.setattr` (auto-reverted at
teardown) rather than mutating the global provider_registry, matching
services/api/tests/test_flights_live_search.py's (T-038) pattern.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

import ai.discovery.accommodation.accommodation_intelligence as acc_module
from travelos.intelligence_gateway.discovery_adapters import GatewayAccommodationProvider
from travelos.intelligence_gateway.gateway import IntelligenceGateway
from travelos.intelligence_gateway.provider_registry import ProviderRegistry
from travelos.live_providers.adapters.duffel_stays_provider import register_duffel_stays_provider
from travelos.live_providers.transport import FakeTransport, TransportResponse

_MODE_VAR = "TRALVANA_ACCOMMODATION_PROVIDER_MODE"
_TOKEN_VAR = "DUFFEL_API_TOKEN"
_FALLBACK_VAR = "TRALVANA_ACCOMMODATION_MOCK_FALLBACK_ENABLED"

_TOMORROW = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")

_PLACES_BODY = {"data": [{"id": "place_1", "type": "city", "name": "Tokyo", "latitude": 35.6762, "longitude": 139.6503}]}

_SEARCH_BODY = {
    "data": {
        "created_at": "2026-07-13T00:00:00Z",
        "results": [
            {
                "id": "sr_039",
                "cheapest_rate_total_amount": "180.00",
                "cheapest_rate_currency": "USD",
                "accommodation": {
                    "id": "acc_039",
                    "name": "Duffel Stays Test Hotel",
                    "rating": 4,
                    "review_score": 8.9,
                    "amenities": ["pool"],
                    "location": {
                        "geographic_coordinates": {"latitude": 35.68, "longitude": 139.65},
                        "address": {"city_name": "Tokyo"},
                    },
                    "rooms": [
                        {
                            "rates": [
                                {
                                    "id": "rate_039", "total_amount": "180.00", "total_currency": "USD",
                                    "board_type": "breakfast",
                                    "cancellation_timeline": [{"refund_amount": "180.00", "currency": "USD", "before": "2026-08-20T00:00:00Z"}],
                                }
                            ]
                        }
                    ],
                },
            }
        ],
    }
}


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv(_MODE_VAR, raising=False)
    monkeypatch.delenv(_TOKEN_VAR, raising=False)
    monkeypatch.delenv(_FALLBACK_VAR, raising=False)


def _responder(search_status=200, search_body=None):
    def respond(request):
        if "places/suggestions" in request.url:
            return TransportResponse(status_code=200, body=_PLACES_BODY)
        return TransportResponse(status_code=search_status, body=search_body)
    return respond


def _install_live_provider(monkeypatch, status_code=200, body=None):
    monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
    monkeypatch.setenv(_TOKEN_VAR, "duffel_test_abc123")
    registry = ProviderRegistry()
    register_duffel_stays_provider(
        transport=FakeTransport(responder=_responder(search_status=status_code, search_body=body)),
        registry=registry,
    )
    gateway = IntelligenceGateway(registry=registry)
    monkeypatch.setattr(acc_module.accommodation_intelligence, "_provider", GatewayAccommodationProvider(gateway=gateway))


class TestMockModeResponseShapeUnchanged:
    def test_response_has_existing_fields(self, client):
        res = client.post("/accommodation/recommend", json={"destination": "Tokyo"})
        assert res.status_code == 201
        body = res.json()
        for field in ("accommodation_options", "assumptions", "next_actions", "recommended_agents", "summary"):
            assert field in body

    def test_response_has_new_safe_metadata_fields_defaulting_sanely(self, client):
        res = client.post("/accommodation/recommend", json={"destination": "Rome"})
        body = res.json()
        assert body["data_source"] == "MOCK"
        assert body["provider_status"] == "AVAILABLE"
        assert body["ranked_results_count"] == len(body["accommodation_options"])

    def test_mock_mode_never_requires_a_check_in_date(self, client):
        res = client.post("/accommodation/recommend", json={"destination": "Tokyo"})
        assert res.status_code == 201

    def test_accommodation_option_never_exposes_provider_ids(self, client):
        res = client.post("/accommodation/recommend", json={"destination": "Rome"})
        for option in res.json()["accommodation_options"]:
            assert "provider_property_id" not in option
            assert "provider_rate_id" not in option
            assert "_provider_property_id" not in option


class TestLiveSandboxValidation:
    def test_empty_destination_returns_422_without_calling_provider(self, client, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        monkeypatch.setenv(_TOKEN_VAR, "duffel_test_abc123")
        res = client.post("/accommodation/recommend", json={"destination": "", "check_in_date": _TOMORROW})
        assert res.status_code == 422
        assert "destination" in str(res.json()["detail"])

    def test_missing_check_in_date_returns_422(self, client, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        monkeypatch.setenv(_TOKEN_VAR, "duffel_test_abc123")
        res = client.post("/accommodation/recommend", json={"destination": "Tokyo"})
        assert res.status_code == 422

    def test_past_check_in_date_returns_422(self, client, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        monkeypatch.setenv(_TOKEN_VAR, "duffel_test_abc123")
        res = client.post("/accommodation/recommend", json={"destination": "Tokyo", "check_in_date": "2020-01-01"})
        assert res.status_code == 422


class TestLiveSandboxEndToEnd:
    def test_valid_live_search_returns_duffel_stays_sandbox_data(self, client, monkeypatch):
        _install_live_provider(monkeypatch, status_code=200, body=_SEARCH_BODY)
        res = client.post("/accommodation/recommend", json={
            "destination": "Tokyo", "check_in_date": _TOMORROW, "nights": 2,
        })
        assert res.status_code == 201
        body = res.json()
        assert body["data_source"] == "DUFFEL_STAYS_SANDBOX"
        assert body["ranked_results_count"] == 1
        assert body["accommodation_options"][0]["property_name"] == "Duffel Stays Test Hotel"
        assert body["request_id"]

    def test_live_search_result_carries_no_secret_or_raw_provider_payload(self, client, monkeypatch):
        _install_live_provider(monkeypatch, status_code=200, body=_SEARCH_BODY)
        res = client.post("/accommodation/recommend", json={
            "destination": "Tokyo", "check_in_date": _TOMORROW, "nights": 2,
        })
        raw = res.text
        assert "duffel_test_abc123" not in raw
        assert "Authorization" not in raw
        assert "Bearer" not in raw
        assert "acc_039" not in raw  # Duffel's raw property id — internal only
        assert "rate_039" not in raw  # Duffel's raw rate id — internal only


class TestLiveSandboxFailureBehaviour:
    def test_unavailable_provider_returns_503_by_default(self, client, monkeypatch):
        _install_live_provider(monkeypatch, status_code=500, body=None)
        res = client.post("/accommodation/recommend", json={
            "destination": "Tokyo", "check_in_date": _TOMORROW, "nights": 2,
        })
        assert res.status_code == 503

    def test_503_response_never_contains_the_token(self, client, monkeypatch):
        _install_live_provider(monkeypatch, status_code=500, body=None)
        res = client.post("/accommodation/recommend", json={
            "destination": "Tokyo", "check_in_date": _TOMORROW, "nights": 2,
        })
        assert "duffel_test_abc123" not in res.text

    def test_fallback_enabled_returns_mock_data_labelled_as_fallback(self, client, monkeypatch):
        monkeypatch.setenv(_FALLBACK_VAR, "true")
        _install_live_provider(monkeypatch, status_code=500, body=None)
        res = client.post("/accommodation/recommend", json={
            "destination": "Tokyo", "check_in_date": _TOMORROW, "nights": 2,
        })
        assert res.status_code == 201
        body = res.json()
        assert body["data_source"] == "MOCK_FALLBACK"
        assert len(body["accommodation_options"]) > 0
        assert any("fallback" in a.lower() for a in body["assumptions"])

    def test_zero_properties_is_not_an_error(self, client, monkeypatch):
        empty_response = {"data": {"id": "orq_empty", "results": []}}
        _install_live_provider(monkeypatch, status_code=200, body=empty_response)
        res = client.post("/accommodation/recommend", json={
            "destination": "Tokyo", "check_in_date": _TOMORROW, "nights": 2,
        })
        assert res.status_code == 201
        body = res.json()
        assert body["data_source"] == "DUFFEL_STAYS_SANDBOX"
        assert body["ranked_results_count"] == 0
        assert body["accommodation_options"] == []
