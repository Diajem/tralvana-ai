"""
Public /flights/recommend behaviour for T-038: response-shape backward
compatibility, LIVE_SANDBOX validation (422) before any provider call,
LIVE_SANDBOX end-to-end through a FakeTransport-backed Duffel provider,
failure/fallback behaviour (503 by default, mock fallback when
enabled), and no secret leakage anywhere in the response.

Live-mode tests swap `flight_intelligence`'s `_provider` for the
duration of one test via `monkeypatch.setattr` (auto-reverted at
teardown) rather than mutating the global provider_registry, so no
state leaks into other tests in this session-scoped-client suite.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

import ai.discovery.flights.flight_intelligence as fi_module
from travelos.intelligence_gateway.discovery_adapters import GatewayFlightProvider
from travelos.intelligence_gateway.gateway import IntelligenceGateway
from travelos.intelligence_gateway.provider_registry import ProviderRegistry
from travelos.live_providers.adapters.duffel_flight_provider import register_duffel_flight_provider
from travelos.live_providers.transport import FakeTransport

_MODE_VAR = "TRALVANA_FLIGHT_PROVIDER_MODE"
_TOKEN_VAR = "DUFFEL_API_TOKEN"
_FALLBACK_VAR = "TRALVANA_FLIGHT_MOCK_FALLBACK_ENABLED"

_TOMORROW = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")

_DUFFEL_OFFER_RESPONSE = {
    "data": {
        "id": "orq_test_038",
        "offers": [
            {
                "id": "off_test_038",
                "total_amount": "312.50",
                "total_currency": "GBP",
                "owner": {"name": "British Airways", "iata_code": "BA"},
                "slices": [
                    {
                        "duration": "PT8H30M",
                        "segments": [
                            {
                                "origin": {"iata_code": "LHR"},
                                "destination": {"iata_code": "JFK"},
                                "departing_at": f"{_TOMORROW}T14:00:00",
                                "arriving_at": f"{_TOMORROW}T22:30:00",
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
                    "change_before_departure": {"allowed": True},
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


def _install_live_provider(monkeypatch, status_code=200, body=None):
    monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
    monkeypatch.setenv(_TOKEN_VAR, "duffel_test_abc123")
    registry = ProviderRegistry()
    register_duffel_flight_provider(
        transport=FakeTransport.always_returning(status_code=status_code, body=body),
        registry=registry,
    )
    gateway = IntelligenceGateway(registry=registry)
    monkeypatch.setattr(fi_module.flight_intelligence, "_provider", GatewayFlightProvider(gateway=gateway))


class TestMockModeResponseShapeUnchanged:
    def test_response_has_existing_fields(self, client):
        res = client.post("/flights/recommend", json={"origin": "London", "destination": "Tokyo"})
        assert res.status_code == 201
        body = res.json()
        for field in ("flight_options", "assumptions", "next_actions", "recommended_agents", "summary"):
            assert field in body

    def test_response_has_new_safe_metadata_fields_defaulting_sanely(self, client):
        res = client.post("/flights/recommend", json={"origin": "London", "destination": "Rome"})
        body = res.json()
        assert body["data_source"] == "MOCK"
        assert body["provider_status"] == "AVAILABLE"
        assert body["results_count"] == len(body["flight_options"])

    def test_mock_mode_never_requires_iata_codes(self, client):
        # Pre-existing, city-name-based requests must keep working exactly
        # as before T-038 — validation is LIVE_SANDBOX-only.
        res = client.post("/flights/recommend", json={"origin": "London", "destination": "Tokyo"})
        assert res.status_code == 201

    def test_flight_option_never_exposes_provider_offer_id(self, client):
        res = client.post("/flights/recommend", json={"origin": "London", "destination": "Rome"})
        for option in res.json()["flight_options"]:
            assert "provider_offer_id" not in option
            assert "_provider_offer_id" not in option


class TestLiveSandboxValidation:
    def test_non_iata_origin_returns_422_without_calling_provider(self, client, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        monkeypatch.setenv(_TOKEN_VAR, "duffel_test_abc123")
        res = client.post("/flights/recommend", json={
            "origin": "London", "destination": "JFK", "departure_date": _TOMORROW,
        })
        assert res.status_code == 422
        assert "origin" in str(res.json()["detail"])

    def test_missing_departure_date_returns_422(self, client, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        monkeypatch.setenv(_TOKEN_VAR, "duffel_test_abc123")
        res = client.post("/flights/recommend", json={"origin": "LHR", "destination": "JFK"})
        assert res.status_code == 422

    def test_past_departure_date_returns_422(self, client, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        monkeypatch.setenv(_TOKEN_VAR, "duffel_test_abc123")
        res = client.post("/flights/recommend", json={
            "origin": "LHR", "destination": "JFK", "departure_date": "2020-01-01",
        })
        assert res.status_code == 422

    def test_same_origin_and_destination_returns_422(self, client, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        monkeypatch.setenv(_TOKEN_VAR, "duffel_test_abc123")
        res = client.post("/flights/recommend", json={
            "origin": "LHR", "destination": "LHR", "departure_date": _TOMORROW,
        })
        assert res.status_code == 422


class TestLiveSandboxEndToEnd:
    def test_valid_live_search_returns_duffel_sandbox_data(self, client, monkeypatch):
        _install_live_provider(monkeypatch, status_code=200, body=_DUFFEL_OFFER_RESPONSE)
        res = client.post("/flights/recommend", json={
            "origin": "LHR", "destination": "JFK", "departure_date": _TOMORROW, "cabin_class": "economy",
        })
        assert res.status_code == 201
        body = res.json()
        assert body["data_source"] == "DUFFEL_SANDBOX"
        assert body["results_count"] == 1
        assert body["flight_options"][0]["airline"] == "British Airways"
        assert body["request_id"]

    def test_live_search_result_carries_no_secret_or_raw_provider_payload(self, client, monkeypatch):
        _install_live_provider(monkeypatch, status_code=200, body=_DUFFEL_OFFER_RESPONSE)
        res = client.post("/flights/recommend", json={
            "origin": "LHR", "destination": "JFK", "departure_date": _TOMORROW, "cabin_class": "economy",
        })
        raw = res.text
        assert "duffel_test_abc123" not in raw
        assert "Authorization" not in raw
        assert "Bearer" not in raw
        assert "off_test_038" not in raw  # Duffel's raw offer id — internal only


class TestLiveSandboxFailureBehaviour:
    def test_unavailable_provider_returns_503_by_default(self, client, monkeypatch):
        _install_live_provider(monkeypatch, status_code=500, body=None)
        res = client.post("/flights/recommend", json={
            "origin": "LHR", "destination": "JFK", "departure_date": _TOMORROW, "cabin_class": "economy",
        })
        assert res.status_code == 503

    def test_503_response_never_contains_the_token(self, client, monkeypatch):
        _install_live_provider(monkeypatch, status_code=500, body=None)
        res = client.post("/flights/recommend", json={
            "origin": "LHR", "destination": "JFK", "departure_date": _TOMORROW, "cabin_class": "economy",
        })
        assert "duffel_test_abc123" not in res.text

    def test_fallback_enabled_returns_mock_data_labelled_as_fallback(self, client, monkeypatch):
        monkeypatch.setenv(_FALLBACK_VAR, "true")
        _install_live_provider(monkeypatch, status_code=500, body=None)
        res = client.post("/flights/recommend", json={
            "origin": "LHR", "destination": "JFK", "departure_date": _TOMORROW, "cabin_class": "economy",
        })
        assert res.status_code == 201
        body = res.json()
        assert body["data_source"] == "MOCK_FALLBACK"
        assert len(body["flight_options"]) > 0
        assert any("fallback" in a.lower() for a in body["assumptions"])

    def test_zero_offers_is_not_an_error(self, client, monkeypatch):
        empty_response = {"data": {"id": "orq_empty", "offers": []}}
        _install_live_provider(monkeypatch, status_code=200, body=empty_response)
        res = client.post("/flights/recommend", json={
            "origin": "LHR", "destination": "JFK", "departure_date": _TOMORROW, "cabin_class": "economy",
        })
        assert res.status_code == 201
        body = res.json()
        assert body["data_source"] == "DUFFEL_SANDBOX"
        assert body["results_count"] == 0
        assert body["flight_options"] == []
