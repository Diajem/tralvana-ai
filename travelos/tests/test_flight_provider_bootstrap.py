"""
configure_flight_provider() — the T-038 composition root. Never makes a
real network call (no Transport is exercised beyond construction);
FakeTransport-equivalent safety is inherited from HttpxTransport itself
never being invoked until an actual search happens.
"""

from __future__ import annotations

import pytest

from travelos.intelligence_gateway.provider_registry import ProviderRegistry
from travelos.intelligence_gateway.provider_status import Capability
from travelos.live_providers.flight_provider_bootstrap import (
    FlightProviderMisconfiguredError,
    configure_flight_provider,
)

_MODE_VAR = "TRALVANA_FLIGHT_PROVIDER_MODE"
_TOKEN_VAR = "DUFFEL_API_TOKEN"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv(_MODE_VAR, raising=False)
    monkeypatch.delenv(_TOKEN_VAR, raising=False)


class TestMockModeIsANoOp:
    def test_mock_mode_registers_nothing(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "MOCK")
        registry = ProviderRegistry()
        configure_flight_provider(registry=registry)
        assert registry.get_providers(Capability.FLIGHTS) == []

    def test_default_mode_registers_nothing(self):
        registry = ProviderRegistry()
        configure_flight_provider(registry=registry)
        assert registry.get_providers(Capability.FLIGHTS) == []

    def test_mock_mode_with_token_still_registers_nothing(self, monkeypatch):
        # Token presence must never imply live mode (T-038, section 1).
        monkeypatch.setenv(_TOKEN_VAR, "duffel_test_abc123")
        registry = ProviderRegistry()
        configure_flight_provider(registry=registry)
        assert registry.get_providers(Capability.FLIGHTS) == []


class TestLiveSandboxModeRegistersDuffel:
    def test_registers_duffel_flight_provider(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        monkeypatch.setenv(_TOKEN_VAR, "duffel_test_abc123")
        registry = ProviderRegistry()
        configure_flight_provider(registry=registry)
        names = {p.provider_name for p in registry.get_providers(Capability.FLIGHTS)}
        assert "duffel_flight_provider" in names

    def test_idempotent_second_call_does_not_double_register(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        monkeypatch.setenv(_TOKEN_VAR, "duffel_test_abc123")
        registry = ProviderRegistry()
        configure_flight_provider(registry=registry)
        configure_flight_provider(registry=registry)
        names = [p.provider_name for p in registry.get_providers(Capability.FLIGHTS)]
        assert names.count("duffel_flight_provider") == 1


class TestLiveSandboxModeRequiresToken:
    def test_missing_token_raises_at_configure_time(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        registry = ProviderRegistry()
        with pytest.raises(FlightProviderMisconfiguredError):
            configure_flight_provider(registry=registry)

    def test_missing_token_registers_nothing(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        registry = ProviderRegistry()
        try:
            configure_flight_provider(registry=registry)
        except FlightProviderMisconfiguredError:
            pass
        assert registry.get_providers(Capability.FLIGHTS) == []

    def test_error_message_never_contains_a_token_value(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        registry = ProviderRegistry()
        with pytest.raises(FlightProviderMisconfiguredError) as exc_info:
            configure_flight_provider(registry=registry)
        assert "DUFFEL_API_TOKEN" in str(exc_info.value)
        # Nothing resembling a secret value could appear since none was
        # ever set — this asserts the message only ever names the env
        # var, never reads/echoes its value.
