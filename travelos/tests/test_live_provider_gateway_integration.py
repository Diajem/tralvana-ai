"""
Proves the Intelligence Gateway (T-025) already supports live providers
(T-026) with zero changes to gateway.py/provider_registry.py/provider_selector.py
— a BaseLiveProvider subclass is just another Provider, selected,
retried, and failed over by the exact same code a mock provider uses
(docs/ADR/ADR-021-live-provider-framework.md).
"""

from __future__ import annotations


import pytest

from travelos.intelligence_gateway.gateway import IntelligenceGateway
from travelos.intelligence_gateway.provider_contract import ProviderRequest
from travelos.intelligence_gateway.provider_registry import ProviderRegistry
from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_status import Capability, ProviderEnvironment, ProviderStatus
from travelos.live_providers.templates.example_flight_provider import ExampleFlightProvider

_ENV_VAR = "EXAMPLE_AIRLINE_API_KEY"


class _MockFlightStub:
    """Minimal stand-in for a T-025 mock provider — avoids depending on
    the real registered mock_flight_provider singleton for test isolation."""
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


def _req():
    return ProviderRequest(
        capability=Capability.FLIGHTS, operation="search",
        params={"origin": "LON", "destination": "Tokyo", "departure_date": "2026-10-01"},
    )


class TestMockAndLiveRegisteredTogether:
    def test_both_registrable_in_the_same_registry(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        registry = ProviderRegistry()
        registry.register(_MockFlightStub())
        registry.register(ExampleFlightProvider())
        names = {p.provider_name for p in registry.get_providers(Capability.FLIGHTS)}
        assert "stub_mock_flight_provider" in names
        assert "example_flight_provider_template" in names


class TestEnvironmentBasedSelection:
    def test_mock_environment_selects_only_the_mock_provider(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        registry = ProviderRegistry()
        registry.register(_MockFlightStub())
        registry.register(ExampleFlightProvider())
        gw = IntelligenceGateway(registry=registry, environment=ProviderEnvironment.MOCK)

        result = gw.execute(Capability.FLIGHTS, _req())
        assert result.provider_name == "stub_mock_flight_provider"

    def test_sandbox_environment_selects_only_the_live_provider(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        registry = ProviderRegistry()
        registry.register(_MockFlightStub())
        registry.register(ExampleFlightProvider())
        gw = IntelligenceGateway(registry=registry, environment=ProviderEnvironment.SANDBOX)

        result = gw.execute(Capability.FLIGHTS, _req())
        assert result.provider_name == "example_flight_provider_template"


class TestFailoverFromLiveToMock:
    def test_misconfigured_live_provider_is_ineligible_not_a_hard_failure(self, monkeypatch):
        # No API key set — the live provider reports MISCONFIGURED via
        # health_check() and is filtered out by the selector entirely
        # (never even attempted, let alone retried), yielding a clean
        # UNAVAILABLE result rather than raising.
        registry = ProviderRegistry()
        registry.register(ExampleFlightProvider())
        gw = IntelligenceGateway(registry=registry, environment=ProviderEnvironment.SANDBOX)

        result = gw.execute(Capability.FLIGHTS, _req())
        assert result.status == ProviderStatus.UNAVAILABLE

    def test_live_provider_failure_falls_over_to_mock_when_both_share_an_environment(self, monkeypatch):
        # This is the realistic failover scenario for a future mixed
        # deployment: both providers registered as MOCK-environment
        # eligible isn't how T-026 scopes live providers (SANDBOX/
        # PRODUCTION only), so failover across environments is
        # demonstrated at the ProviderSelector/failover_policy level
        # directly instead — see test_gateway.py's TestFailover for the
        # general mechanism, already proven provider-type-agnostic.
        from travelos.intelligence_gateway.failover_policy import run_with_failover

        monkeypatch.setenv(_ENV_VAR, "test-key")
        live = ExampleFlightProvider()
        # Force the live provider's transport to fail every call.
        from travelos.live_providers.transport import FakeTransport
        live._transport = FakeTransport.always_returning(status_code=503)
        mock_stub = _MockFlightStub()

        def call(provider, req):
            return provider.execute(req)

        outcome = run_with_failover([live, mock_stub], _req(), call)
        assert outcome.provider_used == "stub_mock_flight_provider"
        assert any("example_flight_provider_template" in w for w in outcome.warnings)


class TestHealthAffectsEligibility:
    def test_unconfigured_live_provider_excluded_from_selection(self, monkeypatch):
        from travelos.intelligence_gateway.provider_selector import ProviderSelector

        live = ExampleFlightProvider()  # no API key set
        selector = ProviderSelector()
        eligible = selector.select([live], _req(), ProviderEnvironment.SANDBOX)
        assert eligible == []

    def test_configured_live_provider_included_in_selection(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        from travelos.intelligence_gateway.provider_selector import ProviderSelector

        live = ExampleFlightProvider()
        selector = ProviderSelector()
        eligible = selector.select([live], _req(), ProviderEnvironment.SANDBOX)
        assert eligible == [live]
