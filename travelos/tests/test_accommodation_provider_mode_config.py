"""TRALVANA_ACCOMMODATION_PROVIDER_MODE / TRALVANA_ACCOMMODATION_MOCK_FALLBACK_ENABLED
(T-039) — scoped to ACCOMMODATION only, independent of provider_environment
and of flight_provider_mode."""

from __future__ import annotations

import pytest

from travelos.config.configuration_manager import config


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("TRALVANA_ACCOMMODATION_PROVIDER_MODE", raising=False)
    monkeypatch.delenv("TRALVANA_ACCOMMODATION_MOCK_FALLBACK_ENABLED", raising=False)
    monkeypatch.delenv("TRALVANA_FLIGHT_PROVIDER_MODE", raising=False)


class TestAccommodationProviderMode:
    def test_defaults_to_mock(self):
        assert config.accommodation_provider_mode == "MOCK"

    def test_explicit_live_sandbox(self, monkeypatch):
        monkeypatch.setenv("TRALVANA_ACCOMMODATION_PROVIDER_MODE", "LIVE_SANDBOX")
        assert config.accommodation_provider_mode == "LIVE_SANDBOX"

    def test_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("TRALVANA_ACCOMMODATION_PROVIDER_MODE", "live_sandbox")
        assert config.accommodation_provider_mode == "LIVE_SANDBOX"

    def test_unrecognised_value_falls_back_to_mock(self, monkeypatch):
        monkeypatch.setenv("TRALVANA_ACCOMMODATION_PROVIDER_MODE", "PRODUCTION")
        assert config.accommodation_provider_mode == "MOCK"

    def test_never_inferred_from_token_presence(self, monkeypatch):
        monkeypatch.setenv("DUFFEL_API_TOKEN", "duffel_test_abc123")
        assert config.accommodation_provider_mode == "MOCK"

    def test_independent_of_flight_provider_mode(self, monkeypatch):
        monkeypatch.setenv("TRALVANA_FLIGHT_PROVIDER_MODE", "LIVE_SANDBOX")
        assert config.accommodation_provider_mode == "MOCK"


class TestAccommodationMockFallbackEnabled:
    def test_defaults_to_false(self):
        assert config.accommodation_mock_fallback_enabled is False

    def test_explicit_true(self, monkeypatch):
        monkeypatch.setenv("TRALVANA_ACCOMMODATION_MOCK_FALLBACK_ENABLED", "true")
        assert config.accommodation_mock_fallback_enabled is True
