from __future__ import annotations

import pytest

from travelos.config.configuration_manager import config
from travelos.intelligence_gateway.gateway import IntelligenceGateway
from travelos.intelligence_gateway.provider_contract import ProviderRequest
from travelos.intelligence_gateway.provider_registry import ProviderRegistry
from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_status import (
    Capability,
    ProviderEnvironment,
    ProviderStatus,
)

_MODE = "TRALVANA_EVENT_PROVIDER_MODE"
_FALLBACK = "TRALVANA_EVENT_MOCK_FALLBACK_ENABLED"


class _Stub:
    provider_name = "live_events"
    capability = Capability.EVENTS
    environment = ProviderEnvironment.PRODUCTION
    priority = 10

    def health_check(self):
        return ProviderStatus.AVAILABLE

    def supports(self, request):
        return request.capability == self.capability

    def execute(self, request):
        return ProviderResult(
            provider_name=self.provider_name,
            capability=self.capability,
            status=ProviderStatus.AVAILABLE,
            data=[],
        )


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv(_MODE, raising=False)
    monkeypatch.delenv(_FALLBACK, raising=False)


def test_event_mode_defaults_to_mock():
    assert config.event_provider_mode == "MOCK"


def test_event_mode_accepts_live_case_insensitively(monkeypatch):
    monkeypatch.setenv(_MODE, "live")
    assert config.event_provider_mode == "LIVE"


def test_unknown_event_mode_fails_closed(monkeypatch):
    monkeypatch.setenv(_MODE, "production")
    assert config.event_provider_mode == "MOCK"


def test_event_fallback_defaults_false(monkeypatch):
    assert config.event_mock_fallback_enabled is False
    monkeypatch.setenv(_FALLBACK, "true")
    assert config.event_mock_fallback_enabled is True


def test_live_mode_selects_production_event_provider(monkeypatch):
    monkeypatch.setenv(_MODE, "LIVE")
    registry = ProviderRegistry()
    registry.register(_Stub())
    gateway = IntelligenceGateway(registry=registry)
    result = gateway.execute(
        Capability.EVENTS,
        ProviderRequest(capability=Capability.EVENTS, operation="search"),
    )
    assert result.provider_name == "live_events"


def test_explicit_test_environment_override_still_wins(monkeypatch):
    monkeypatch.setenv(_MODE, "LIVE")
    registry = ProviderRegistry()
    registry.register(_Stub())
    gateway = IntelligenceGateway(
        registry=registry,
        environment=ProviderEnvironment.MOCK,
    )
    result = gateway.execute(
        Capability.EVENTS,
        ProviderRequest(capability=Capability.EVENTS, operation="search"),
    )
    assert result.status == ProviderStatus.UNAVAILABLE
