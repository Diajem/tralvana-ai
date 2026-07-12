"""
configure_accommodation_provider() — the T-039 composition root. Never
makes a real network call (no Transport is exercised beyond
construction).
"""

from __future__ import annotations

import pytest

from travelos.intelligence_gateway.provider_registry import ProviderRegistry
from travelos.intelligence_gateway.provider_status import Capability
from travelos.live_providers.accommodation_provider_bootstrap import (
    AccommodationProviderMisconfiguredError,
    configure_accommodation_provider,
)

_MODE_VAR = "TRALVANA_ACCOMMODATION_PROVIDER_MODE"
_TOKEN_VAR = "DUFFEL_API_TOKEN"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv(_MODE_VAR, raising=False)
    monkeypatch.delenv(_TOKEN_VAR, raising=False)


class TestMockModeIsANoOp:
    def test_mock_mode_registers_nothing(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "MOCK")
        registry = ProviderRegistry()
        configure_accommodation_provider(registry=registry)
        assert registry.get_providers(Capability.ACCOMMODATION) == []

    def test_default_mode_registers_nothing(self):
        registry = ProviderRegistry()
        configure_accommodation_provider(registry=registry)
        assert registry.get_providers(Capability.ACCOMMODATION) == []

    def test_mock_mode_with_token_still_registers_nothing(self, monkeypatch):
        monkeypatch.setenv(_TOKEN_VAR, "duffel_test_abc123")
        registry = ProviderRegistry()
        configure_accommodation_provider(registry=registry)
        assert registry.get_providers(Capability.ACCOMMODATION) == []


class TestLiveSandboxModeRegistersDuffelStays:
    def test_registers_duffel_stays_provider(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        monkeypatch.setenv(_TOKEN_VAR, "duffel_test_abc123")
        registry = ProviderRegistry()
        configure_accommodation_provider(registry=registry)
        names = {p.provider_name for p in registry.get_providers(Capability.ACCOMMODATION)}
        assert "duffel_stays_provider" in names

    def test_idempotent_second_call_does_not_double_register(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        monkeypatch.setenv(_TOKEN_VAR, "duffel_test_abc123")
        registry = ProviderRegistry()
        configure_accommodation_provider(registry=registry)
        configure_accommodation_provider(registry=registry)
        names = [p.provider_name for p in registry.get_providers(Capability.ACCOMMODATION)]
        assert names.count("duffel_stays_provider") == 1


class TestLiveSandboxModeRequiresToken:
    def test_missing_token_raises_at_configure_time(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        registry = ProviderRegistry()
        with pytest.raises(AccommodationProviderMisconfiguredError):
            configure_accommodation_provider(registry=registry)

    def test_missing_token_registers_nothing(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        registry = ProviderRegistry()
        try:
            configure_accommodation_provider(registry=registry)
        except AccommodationProviderMisconfiguredError:
            pass
        assert registry.get_providers(Capability.ACCOMMODATION) == []

    def test_error_message_never_contains_a_token_value(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        registry = ProviderRegistry()
        with pytest.raises(AccommodationProviderMisconfiguredError) as exc_info:
            configure_accommodation_provider(registry=registry)
        assert "DUFFEL_API_TOKEN" in str(exc_info.value)
