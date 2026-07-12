"""
IntelligenceGateway's per-capability environment resolution (T-038) —
FLIGHTS reads TRALVANA_FLIGHT_PROVIDER_MODE, independent of the general
PROVIDER_ENVIRONMENT which still governs every other capability.
"""

from __future__ import annotations

import pytest

from travelos.intelligence_gateway.gateway import IntelligenceGateway
from travelos.intelligence_gateway.provider_contract import ProviderRequest
from travelos.intelligence_gateway.provider_registry import ProviderRegistry
from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_status import Capability, ProviderEnvironment, ProviderStatus


class _Stub:
    def __init__(self, name: str, capability: Capability, environment: ProviderEnvironment) -> None:
        self.provider_name = name
        self.capability = capability
        self.environment = environment
        self.priority = 50

    def health_check(self):
        return ProviderStatus.AVAILABLE

    def supports(self, request):
        return request.capability == self.capability

    def execute(self, request):
        return ProviderResult(
            provider_name=self.provider_name, capability=self.capability,
            status=ProviderStatus.AVAILABLE, data=[{"stub": True}], confidence=1.0,
        )


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("TRALVANA_FLIGHT_PROVIDER_MODE", raising=False)
    monkeypatch.delenv("PROVIDER_ENVIRONMENT", raising=False)
    monkeypatch.delenv("TRALVANA_PROVIDER_ENVIRONMENT", raising=False)


def _req(capability: Capability) -> ProviderRequest:
    return ProviderRequest(capability=capability, operation="search", params={})


class TestFlightsUsesFlightProviderMode:
    def test_flights_mock_mode_selects_mock_flight_provider(self, monkeypatch):
        monkeypatch.setenv("TRALVANA_FLIGHT_PROVIDER_MODE", "MOCK")
        registry = ProviderRegistry()
        registry.register(_Stub("mock_flights", Capability.FLIGHTS, ProviderEnvironment.MOCK))
        registry.register(_Stub("live_flights", Capability.FLIGHTS, ProviderEnvironment.SANDBOX))
        gw = IntelligenceGateway(registry=registry)

        result = gw.execute(Capability.FLIGHTS, _req(Capability.FLIGHTS))
        assert result.provider_name == "mock_flights"

    def test_flights_live_sandbox_mode_selects_sandbox_flight_provider(self, monkeypatch):
        monkeypatch.setenv("TRALVANA_FLIGHT_PROVIDER_MODE", "LIVE_SANDBOX")
        registry = ProviderRegistry()
        registry.register(_Stub("mock_flights", Capability.FLIGHTS, ProviderEnvironment.MOCK))
        registry.register(_Stub("live_flights", Capability.FLIGHTS, ProviderEnvironment.SANDBOX))
        gw = IntelligenceGateway(registry=registry)

        result = gw.execute(Capability.FLIGHTS, _req(Capability.FLIGHTS))
        assert result.provider_name == "live_flights"


class TestOtherCapabilitiesUnaffected:
    def test_accommodation_still_uses_general_provider_environment(self, monkeypatch):
        # FLIGHTS is set to LIVE_SANDBOX — accommodation must stay MOCK,
        # since PROVIDER_ENVIRONMENT (unset here) defaults to MOCK and is
        # a completely separate knob.
        monkeypatch.setenv("TRALVANA_FLIGHT_PROVIDER_MODE", "LIVE_SANDBOX")
        registry = ProviderRegistry()
        registry.register(_Stub("mock_accom", Capability.ACCOMMODATION, ProviderEnvironment.MOCK))
        gw = IntelligenceGateway(registry=registry)

        result = gw.execute(Capability.ACCOMMODATION, _req(Capability.ACCOMMODATION))
        assert result.provider_name == "mock_accom"
        assert result.status == ProviderStatus.AVAILABLE

    def test_weather_unaffected_by_flight_provider_mode(self, monkeypatch):
        monkeypatch.setenv("TRALVANA_FLIGHT_PROVIDER_MODE", "LIVE_SANDBOX")
        registry = ProviderRegistry()
        registry.register(_Stub("mock_weather", Capability.WEATHER, ProviderEnvironment.MOCK))
        gw = IntelligenceGateway(registry=registry)

        result = gw.execute(Capability.WEATHER, _req(Capability.WEATHER))
        assert result.provider_name == "mock_weather"


class TestExplicitOverrideStillWins:
    def test_constructor_environment_override_beats_flight_provider_mode(self, monkeypatch):
        monkeypatch.setenv("TRALVANA_FLIGHT_PROVIDER_MODE", "LIVE_SANDBOX")
        registry = ProviderRegistry()
        registry.register(_Stub("mock_flights", Capability.FLIGHTS, ProviderEnvironment.MOCK))
        registry.register(_Stub("live_flights", Capability.FLIGHTS, ProviderEnvironment.SANDBOX))
        # Explicit override (used throughout the existing test suite) —
        # must still force MOCK regardless of the env var.
        gw = IntelligenceGateway(registry=registry, environment=ProviderEnvironment.MOCK)

        result = gw.execute(Capability.FLIGHTS, _req(Capability.FLIGHTS))
        assert result.provider_name == "mock_flights"
