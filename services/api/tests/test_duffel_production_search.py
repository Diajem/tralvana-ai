"""Live search uses production providers, real request schemas and truthful labels."""

from datetime import date, timedelta

import pytest

import ai.discovery.accommodation.accommodation_intelligence as stays_module
import ai.discovery.flights.flight_intelligence as flights_module
from ai.trip_brain.trip_assembly import TripAssemblyEngine
from travelos.intelligence_gateway.discovery_adapters import GatewayAccommodationProvider, GatewayFlightProvider
from travelos.intelligence_gateway.gateway import IntelligenceGateway
from travelos.intelligence_gateway.provider_registry import ProviderRegistry
from travelos.intelligence_gateway.provider_status import Capability, ProviderEnvironment
from travelos.live_providers.accommodation_provider_bootstrap import configure_accommodation_provider
from travelos.live_providers.duffel_credentials import duffel_token_variable
from travelos.live_providers.flight_provider_bootstrap import configure_flight_provider
from travelos.live_providers.transport import FakeTransport, TransportResponse
from travelos.tests.test_duffel_stays_provider import _DIRECT_RESULT, _PLACES_BODY, _search_body
from services.api.tests.test_flights_live_search import _DUFFEL_OFFER_RESPONSE


@pytest.fixture
def live_providers(monkeypatch):
    monkeypatch.setenv("TRALVANA_FLIGHT_PROVIDER_MODE", "LIVE")
    monkeypatch.setenv("TRALVANA_ACCOMMODATION_PROVIDER_MODE", "LIVE")
    monkeypatch.setenv("DUFFEL_API_TOKEN", "duffel_test_old_shared")
    monkeypatch.setenv("DUFFEL_FLIGHTS_API_TOKEN", "duffel_live_flights_fixture")
    monkeypatch.setenv("DUFFEL_STAYS_API_TOKEN", "duffel_live_stays_fixture")
    monkeypatch.setenv("TRALVANA_FLIGHT_MOCK_FALLBACK_ENABLED", "false")
    monkeypatch.setenv("TRALVANA_ACCOMMODATION_MOCK_FALLBACK_ENABLED", "false")

    def respond(request):
        if "places/suggestions" in request.url:
            return TransportResponse(status_code=200, body=_PLACES_BODY)
        if request.url.endswith("/stays/search"):
            assert request.headers["Authorization"] == "Bearer duffel_live_stays_fixture"
            assert set(request.json_body) == {"data"}
            assert request.json_body["data"]["guests"] == [
                {"type": "adult"}, {"type": "adult"}, {"type": "child", "age": 7},
            ]
            return TransportResponse(status_code=200, body=_search_body(_DIRECT_RESULT))
        assert request.headers["Authorization"] == "Bearer duffel_live_flights_fixture"
        return TransportResponse(status_code=201, body=_DUFFEL_OFFER_RESPONSE)

    transport = FakeTransport(responder=respond)
    monkeypatch.setattr("travelos.live_providers.flight_provider_bootstrap.HttpxTransport", lambda: transport)
    registry = ProviderRegistry()
    configure_flight_provider(registry=registry)
    configure_accommodation_provider(registry=registry, transport=transport)
    for capability in (Capability.FLIGHTS, Capability.ACCOMMODATION):
        assert registry.get_providers(capability)[0].environment == ProviderEnvironment.PRODUCTION
    gateway = IntelligenceGateway(registry=registry)
    monkeypatch.setattr(flights_module.flight_intelligence, "_provider", GatewayFlightProvider(gateway))
    monkeypatch.setattr(stays_module.accommodation_intelligence, "_provider", GatewayAccommodationProvider(gateway))
    return transport


@pytest.mark.parametrize("domain,source", [("flights", "DUFFEL_LIVE"), ("accommodation", "DUFFEL_STAYS_LIVE")])
def test_live_search_through_api_and_planner_grounding(client, live_providers, domain, source):
    future = (date.today() + timedelta(days=30)).isoformat()
    payload = (
        {"origin": "LHR", "destination": "JFK", "departure_date": future, "adults": 2}
        if domain == "flights" else
        {"destination": "Tokyo", "check_in_date": future, "nights": 3,
         "adults": 2, "children": 1, "child_ages": [7], "rooms": 1}
    )
    response = client.post(f"/{domain}/recommend", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["data_source"] == source
    options = body["flight_options" if domain == "flights" else "accommodation_options"]
    assert options and all(option["data_source"] == source for option in options)
    assert not any("mock" in a.lower() or "sandbox" in a.lower() for a in body["assumptions"])
    assert not any("has not been checked" in action for action in body["next_actions"])
    assert "duffel_live_" not in response.text
    notice = TripAssemblyEngine()._provider_notice("flight" if domain == "flights" else domain, body)
    assert notice.level == "LIVE" and notice.is_current and notice.requires_confirmation
    assert all("orders" not in r.url and "bookings" not in r.url for r in live_providers.sent_requests)


@pytest.mark.parametrize("product", ["flights", "stays"])
@pytest.mark.parametrize("live,token", [(True, "duffel_test_example"), (False, "duffel_live_example")])
def test_wrong_environment_credentials_fail_without_exposing_token(monkeypatch, product, live, token):
    monkeypatch.setenv(f"DUFFEL_{product.upper()}_API_TOKEN", token)
    with pytest.raises(ValueError) as exc:
        duffel_token_variable(product, live)
    assert token not in str(exc.value)


def test_empty_dedicated_credential_does_not_fall_back_to_another_account(monkeypatch):
    monkeypatch.setenv("DUFFEL_API_TOKEN", "duffel_live_other_account")
    monkeypatch.setenv("DUFFEL_STAYS_API_TOKEN", "")
    with pytest.raises(ValueError):
        duffel_token_variable("stays", True)


def test_live_invalid_child_age_stops_before_network(client, live_providers):
    response = client.post("/accommodation/recommend", json={
        "destination": "Tokyo", "check_in_date": (date.today() + timedelta(days=30)).isoformat(),
        "adults": 2, "children": 1, "child_ages": [], "nights": 3,
    })
    assert response.status_code == 422
    assert live_providers.sent_requests == []
