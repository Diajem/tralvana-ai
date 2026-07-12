"""
IntelligenceGateway's per-capability environment resolution, extended
in T-039 to ACCOMMODATION — reads TRALVANA_ACCOMMODATION_PROVIDER_MODE,
independent of FLIGHTS' own switch and of the general PROVIDER_ENVIRONMENT
which still governs Weather.
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
    monkeypatch.delenv("TRALVANA_ACCOMMODATION_PROVIDER_MODE", raising=False)
    monkeypatch.delenv("TRALVANA_FLIGHT_PROVIDER_MODE", raising=False)
    monkeypatch.delenv("PROVIDER_ENVIRONMENT", raising=False)
    monkeypatch.delenv("TRALVANA_PROVIDER_ENVIRONMENT", raising=False)


def _req(capability: Capability) -> ProviderRequest:
    return ProviderRequest(capability=capability, operation="search", params={})


class TestAccommodationUsesItsOwnProviderMode:
    def test_mock_mode_selects_mock_accommodation_provider(self, monkeypatch):
        monkeypatch.setenv("TRALVANA_ACCOMMODATION_PROVIDER_MODE", "MOCK")
        registry = ProviderRegistry()
        registry.register(_Stub("mock_accom", Capability.ACCOMMODATION, ProviderEnvironment.MOCK))
        registry.register(_Stub("live_accom", Capability.ACCOMMODATION, ProviderEnvironment.SANDBOX))
        gw = IntelligenceGateway(registry=registry)

        result = gw.execute(Capability.ACCOMMODATION, _req(Capability.ACCOMMODATION))
        assert result.provider_name == "mock_accom"

    def test_live_sandbox_mode_selects_sandbox_accommodation_provider(self, monkeypatch):
        monkeypatch.setenv("TRALVANA_ACCOMMODATION_PROVIDER_MODE", "LIVE_SANDBOX")
        registry = ProviderRegistry()
        registry.register(_Stub("mock_accom", Capability.ACCOMMODATION, ProviderEnvironment.MOCK))
        registry.register(_Stub("live_accom", Capability.ACCOMMODATION, ProviderEnvironment.SANDBOX))
        gw = IntelligenceGateway(registry=registry)

        result = gw.execute(Capability.ACCOMMODATION, _req(Capability.ACCOMMODATION))
        assert result.provider_name == "live_accom"


class TestIndependenceFromOtherCapabilities:
    def test_flights_live_mode_does_not_affect_accommodation(self, monkeypatch):
        monkeypatch.setenv("TRALVANA_FLIGHT_PROVIDER_MODE", "LIVE_SANDBOX")
        registry = ProviderRegistry()
        registry.register(_Stub("mock_accom", Capability.ACCOMMODATION, ProviderEnvironment.MOCK))
        gw = IntelligenceGateway(registry=registry)
        result = gw.execute(Capability.ACCOMMODATION, _req(Capability.ACCOMMODATION))
        assert result.provider_name == "mock_accom"

    def test_accommodation_live_mode_does_not_affect_weather(self, monkeypatch):
        monkeypatch.setenv("TRALVANA_ACCOMMODATION_PROVIDER_MODE", "LIVE_SANDBOX")
        registry = ProviderRegistry()
        registry.register(_Stub("mock_weather", Capability.WEATHER, ProviderEnvironment.MOCK))
        gw = IntelligenceGateway(registry=registry)
        result = gw.execute(Capability.WEATHER, _req(Capability.WEATHER))
        assert result.provider_name == "mock_weather"

    def test_accommodation_live_mode_does_not_affect_flights(self, monkeypatch):
        monkeypatch.setenv("TRALVANA_ACCOMMODATION_PROVIDER_MODE", "LIVE_SANDBOX")
        registry = ProviderRegistry()
        registry.register(_Stub("mock_flights", Capability.FLIGHTS, ProviderEnvironment.MOCK))
        gw = IntelligenceGateway(registry=registry)
        result = gw.execute(Capability.FLIGHTS, _req(Capability.FLIGHTS))
        assert result.provider_name == "mock_flights"


class TestExplicitOverrideStillWins:
    def test_constructor_environment_override_beats_accommodation_provider_mode(self, monkeypatch):
        monkeypatch.setenv("TRALVANA_ACCOMMODATION_PROVIDER_MODE", "LIVE_SANDBOX")
        registry = ProviderRegistry()
        registry.register(_Stub("mock_accom", Capability.ACCOMMODATION, ProviderEnvironment.MOCK))
        registry.register(_Stub("live_accom", Capability.ACCOMMODATION, ProviderEnvironment.SANDBOX))
        gw = IntelligenceGateway(registry=registry, environment=ProviderEnvironment.MOCK)

        result = gw.execute(Capability.ACCOMMODATION, _req(Capability.ACCOMMODATION))
        assert result.provider_name == "mock_accom"
