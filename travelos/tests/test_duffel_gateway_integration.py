"""
Proves DuffelFlightProvider (T-027) is a real drop-in Provider exactly
like the T-026 template — registers alongside a mock flight stub,
selected only in SANDBOX, and fails over to mock on a Duffel outage.
Same shape as travelos/tests/test_live_provider_gateway_integration.py,
specific to the concrete adapter this task ships. No real network call
anywhere — FakeTransport only.
"""

from __future__ import annotations

import pytest

from travelos.intelligence_gateway.gateway import IntelligenceGateway
from travelos.intelligence_gateway.provider_contract import ProviderRequest
from travelos.intelligence_gateway.provider_registry import ProviderRegistry
from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_status import Capability, ProviderEnvironment, ProviderStatus
from travelos.live_providers.adapters.duffel_flight_provider import (
    DuffelFlightProvider,
    register_duffel_flight_provider,
)
from travelos.live_providers.transport import FakeTransport

_ENV_VAR = "DUFFEL_API_TOKEN"

_OFFER_REQUEST_RESPONSE = {
    "data": {
        "id": "orq_test",
        "offers": [
            {
                "id": "off_test",
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
                    "change_before_departure": {"allowed": True},
                },
            }
        ],
    }
}


class _MockFlightStub:
    provider_name = "stub_mock_flight_provider"
    capability = Capability.FLIGHTS
    environment = ProviderEnvironment.MOCK
    priority = 50

    def health_check(self):
        return ProviderStatus.AVAILABLE

    def supports(self, request):
        return request.capability == Capability.FLIGHTS

    def execute(self, request):
        return ProviderResult(
            provider_name=self.provider_name, capability=Capability.FLIGHTS,
            status=ProviderStatus.AVAILABLE, data=[{"airline": "Stub Air"}], confidence=1.0,
        )


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv(_ENV_VAR, raising=False)


def _req() -> ProviderRequest:
    return ProviderRequest(
        capability=Capability.FLIGHTS, operation="search",
        params={"origin": "LHR", "destination": "JFK", "departure_date": "2026-10-01",
                "return_date": None, "cabin_class": "economy"},
    )


class TestRegistration:
    def test_register_duffel_flight_provider_adds_it_to_the_registry(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        registry = ProviderRegistry()
        register_duffel_flight_provider(transport=FakeTransport(), registry=registry)
        names = {p.provider_name for p in registry.get_providers(Capability.FLIGHTS)}
        assert "duffel_flight_provider" in names

    def test_mock_and_duffel_coexist_in_the_same_registry(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        registry = ProviderRegistry()
        registry.register(_MockFlightStub())
        register_duffel_flight_provider(transport=FakeTransport(), registry=registry)
        assert len(registry.get_providers(Capability.FLIGHTS)) == 2


class TestEnvironmentBasedSelection:
    def test_mock_environment_never_selects_duffel(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        registry = ProviderRegistry()
        registry.register(_MockFlightStub())
        register_duffel_flight_provider(
            transport=FakeTransport.always_returning(status_code=200, body=_OFFER_REQUEST_RESPONSE),
            registry=registry,
        )
        gw = IntelligenceGateway(registry=registry, environment=ProviderEnvironment.MOCK)
        result = gw.execute(Capability.FLIGHTS, _req())
        assert result.provider_name == "stub_mock_flight_provider"

    def test_sandbox_environment_selects_duffel(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        registry = ProviderRegistry()
        registry.register(_MockFlightStub())
        register_duffel_flight_provider(
            transport=FakeTransport.always_returning(status_code=200, body=_OFFER_REQUEST_RESPONSE),
            registry=registry,
        )
        gw = IntelligenceGateway(registry=registry, environment=ProviderEnvironment.SANDBOX)
        result = gw.execute(Capability.FLIGHTS, _req())
        assert result.provider_name == "duffel_flight_provider"
        assert result.data[0]["airline"] == "British Airways"


class TestFailoverAndEligibility:
    def test_missing_token_makes_duffel_ineligible_not_a_hard_failure(self, monkeypatch):
        registry = ProviderRegistry()
        register_duffel_flight_provider(transport=FakeTransport(), registry=registry)
        gw = IntelligenceGateway(registry=registry, environment=ProviderEnvironment.SANDBOX)
        result = gw.execute(Capability.FLIGHTS, _req())
        assert result.status == ProviderStatus.UNAVAILABLE

    def test_duffel_failure_falls_over_to_mock_when_both_share_an_environment(self, monkeypatch):
        # As in test_live_provider_gateway_integration.py: T-027 registers
        # Duffel as SANDBOX-only, so this exercises run_with_failover
        # directly rather than through the environment-filtered gateway,
        # matching that file's own documented rationale.
        from travelos.intelligence_gateway.failover_policy import run_with_failover

        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        duffel = DuffelFlightProvider(transport=FakeTransport.always_returning(status_code=503))
        mock_stub = _MockFlightStub()

        def call(provider, req):
            return provider.execute(req)

        outcome = run_with_failover([duffel, mock_stub], _req(), call)
        assert outcome.provider_used == "stub_mock_flight_provider"
        assert any("duffel_flight_provider" in w for w in outcome.warnings)


class TestGatewayFlightProviderCompatibility:
    """The Discovery-layer entry point (GatewayFlightProvider.search()) is
    untouched by this task — proves Duffel's output survives that same
    call path with no shape mismatch."""

    def test_search_via_gateway_flight_provider_returns_duffel_shaped_options(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "duffel_test_abc123")
        from travelos.intelligence_gateway.discovery_adapters import GatewayFlightProvider

        registry = ProviderRegistry()
        register_duffel_flight_provider(
            transport=FakeTransport.always_returning(status_code=200, body=_OFFER_REQUEST_RESPONSE),
            registry=registry,
        )
        gw = IntelligenceGateway(registry=registry, environment=ProviderEnvironment.SANDBOX)
        provider = GatewayFlightProvider(gateway=gw)

        options = provider.search(
            origin="LHR", destination="JFK", departure_date="2026-10-01",
            return_date=None, cabin_class="economy",
        )
        assert options[0]["airline"] == "British Airways"
        assert options[0]["flight_number"] == "BA117"
