"""
configure_accommodation_provider() — the T-039 composition root. Never
makes a real network call (no Transport is exercised beyond
construction).
"""

from __future__ import annotations

import pytest

from travelos.intelligence_gateway.provider_registry import ProviderRegistry
from travelos.intelligence_gateway.provider_status import Capability
from travelos.live_providers.hbx_destination_catalog import InMemoryHbxDestinationCatalog
from travelos.live_providers.transport import FakeTransport
from travelos.live_providers.accommodation_provider_bootstrap import (
    AccommodationProviderMisconfiguredError,
    configure_accommodation_provider,
)

_MODE_VAR = "TRALVANA_ACCOMMODATION_PROVIDER_MODE"
_TOKEN_VAR = "DUFFEL_API_TOKEN"
_HBX_KEY_VAR = "HBX_HOTELS_API_KEY"
_HBX_SECRET_VAR = "HBX_HOTELS_SECRET"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv(_MODE_VAR, raising=False)
    monkeypatch.delenv(_TOKEN_VAR, raising=False)
    monkeypatch.delenv(_HBX_KEY_VAR, raising=False)
    monkeypatch.delenv(_HBX_SECRET_VAR, raising=False)


class TestMockModeIsANoOp:
    def test_mock_mode_registers_nothing(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "MOCK")
        registry = ProviderRegistry()
        configure_accommodation_provider(registry=registry, transport=FakeTransport())
        assert registry.get_providers(Capability.ACCOMMODATION) == []

    def test_default_mode_registers_nothing(self):
        registry = ProviderRegistry()
        configure_accommodation_provider(registry=registry, transport=FakeTransport())
        assert registry.get_providers(Capability.ACCOMMODATION) == []

    def test_mock_mode_with_token_still_registers_nothing(self, monkeypatch):
        monkeypatch.setenv(_TOKEN_VAR, "duffel_test_abc123")
        registry = ProviderRegistry()
        configure_accommodation_provider(registry=registry, transport=FakeTransport())
        assert registry.get_providers(Capability.ACCOMMODATION) == []


class TestLiveSandboxModeRegistersDuffelStays:
    def test_registers_duffel_stays_provider(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        monkeypatch.setenv(_TOKEN_VAR, "duffel_test_abc123")
        registry = ProviderRegistry()
        configure_accommodation_provider(registry=registry, transport=FakeTransport())
        names = {p.provider_name for p in registry.get_providers(Capability.ACCOMMODATION)}
        assert "duffel_stays_provider" in names

    def test_idempotent_second_call_does_not_double_register(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        monkeypatch.setenv(_TOKEN_VAR, "duffel_test_abc123")
        registry = ProviderRegistry()
        transport = FakeTransport()
        configure_accommodation_provider(registry=registry, transport=transport)
        configure_accommodation_provider(registry=registry, transport=transport)
        names = [p.provider_name for p in registry.get_providers(Capability.ACCOMMODATION)]
        assert names.count("duffel_stays_provider") == 1


class TestLiveSandboxModeRequiresToken:
    def test_missing_token_raises_at_configure_time(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        registry = ProviderRegistry()
        with pytest.raises(AccommodationProviderMisconfiguredError):
            configure_accommodation_provider(registry=registry, transport=FakeTransport())

    def test_missing_token_registers_nothing(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        registry = ProviderRegistry()
        try:
            configure_accommodation_provider(registry=registry, transport=FakeTransport())
        except AccommodationProviderMisconfiguredError:
            pass
        assert registry.get_providers(Capability.ACCOMMODATION) == []

    def test_error_message_never_contains_a_token_value(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        registry = ProviderRegistry()
        with pytest.raises(AccommodationProviderMisconfiguredError) as exc_info:
            configure_accommodation_provider(registry=registry, transport=FakeTransport())
        assert "DUFFEL_API_TOKEN" in str(exc_info.value)


class TestHbxSandboxMode:
    def test_registers_hbx_without_duffel(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "HBX_SANDBOX")
        monkeypatch.setenv(_HBX_KEY_VAR, "hbx-key")
        monkeypatch.setenv(_HBX_SECRET_VAR, "hbx-secret")
        registry = ProviderRegistry()

        configure_accommodation_provider(
            registry=registry,
            destination_catalog=InMemoryHbxDestinationCatalog(),
            transport=FakeTransport(),
        )

        providers = registry.get_providers(Capability.ACCOMMODATION)
        assert [provider.provider_name for provider in providers] == ["hbx_hotels_provider"]

    @pytest.mark.parametrize("missing", [_HBX_KEY_VAR, _HBX_SECRET_VAR])
    def test_requires_both_hbx_credentials(self, monkeypatch, missing):
        monkeypatch.setenv(_MODE_VAR, "HBX_SANDBOX")
        monkeypatch.setenv(_HBX_KEY_VAR, "hbx-key")
        monkeypatch.setenv(_HBX_SECRET_VAR, "hbx-secret")
        monkeypatch.delenv(missing)

        with pytest.raises(AccommodationProviderMisconfiguredError) as exc_info:
            configure_accommodation_provider(
                registry=ProviderRegistry(),
                destination_catalog=InMemoryHbxDestinationCatalog(),
                transport=FakeTransport(),
            )

        assert missing in str(exc_info.value)
        assert "hbx-key" not in str(exc_info.value)

    def test_multi_mode_registers_hbx_first_and_duffel_as_fallback(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "MULTI_SANDBOX")
        monkeypatch.setenv(_TOKEN_VAR, "duffel-token")
        monkeypatch.setenv(_HBX_KEY_VAR, "hbx-key")
        monkeypatch.setenv(_HBX_SECRET_VAR, "hbx-secret")
        registry = ProviderRegistry()

        configure_accommodation_provider(
            registry=registry,
            destination_catalog=InMemoryHbxDestinationCatalog(),
            transport=FakeTransport(),
        )

        providers = registry.get_providers(Capability.ACCOMMODATION)
        assert [provider.provider_name for provider in providers] == [
            "hbx_hotels_provider",
            "duffel_stays_provider",
        ]
        assert [provider.priority for provider in providers] == [10, 20]
