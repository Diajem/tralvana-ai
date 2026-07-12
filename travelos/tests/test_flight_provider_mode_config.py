"""TRALVANA_FLIGHT_PROVIDER_MODE / TRALVANA_FLIGHT_MOCK_FALLBACK_ENABLED
(T-038) — scoped to FLIGHTS only, independent of provider_environment."""

from __future__ import annotations

import pytest

from travelos.config.configuration_manager import config


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("TRALVANA_FLIGHT_PROVIDER_MODE", raising=False)
    monkeypatch.delenv("TRALVANA_FLIGHT_MOCK_FALLBACK_ENABLED", raising=False)


class TestFlightProviderMode:
    def test_defaults_to_mock(self):
        assert config.flight_provider_mode == "MOCK"

    def test_explicit_live_sandbox(self, monkeypatch):
        monkeypatch.setenv("TRALVANA_FLIGHT_PROVIDER_MODE", "LIVE_SANDBOX")
        assert config.flight_provider_mode == "LIVE_SANDBOX"

    def test_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("TRALVANA_FLIGHT_PROVIDER_MODE", "live_sandbox")
        assert config.flight_provider_mode == "LIVE_SANDBOX"

    def test_unrecognised_value_falls_back_to_mock(self, monkeypatch):
        monkeypatch.setenv("TRALVANA_FLIGHT_PROVIDER_MODE", "PRODUCTION")
        assert config.flight_provider_mode == "MOCK"

    def test_never_inferred_from_token_presence(self, monkeypatch):
        monkeypatch.setenv("DUFFEL_API_TOKEN", "duffel_test_abc123")
        assert config.flight_provider_mode == "MOCK"


class TestFlightMockFallbackEnabled:
    def test_defaults_to_false(self):
        assert config.flight_mock_fallback_enabled is False

    def test_explicit_true(self, monkeypatch):
        monkeypatch.setenv("TRALVANA_FLIGHT_MOCK_FALLBACK_ENABLED", "true")
        assert config.flight_mock_fallback_enabled is True

    def test_explicit_false(self, monkeypatch):
        monkeypatch.setenv("TRALVANA_FLIGHT_MOCK_FALLBACK_ENABLED", "false")
        assert config.flight_mock_fallback_enabled is False
