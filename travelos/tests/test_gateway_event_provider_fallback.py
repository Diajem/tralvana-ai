from __future__ import annotations

import pytest

from travelos.intelligence_gateway.discovery_adapters import (
    GatewayEventProvider,
    LiveEventSearchUnavailableError,
    _distinct_event_search_interests,
)
from travelos.intelligence_gateway.gateway import IntelligenceGateway
from travelos.intelligence_gateway.provider_registry import ProviderRegistry
from travelos.intelligence_gateway.provider_status import ProviderStatus

_MODE = "TRALVANA_EVENT_PROVIDER_MODE"
_FALLBACK = "TRALVANA_EVENT_MOCK_FALLBACK_ENABLED"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv(_MODE, raising=False)
    monkeypatch.delenv(_FALLBACK, raising=False)


def _provider() -> GatewayEventProvider:
    return GatewayEventProvider(
        gateway=IntelligenceGateway(registry=ProviderRegistry())
    )


def test_mock_mode_keeps_quiet_empty_result(monkeypatch):
    monkeypatch.setenv(_MODE, "MOCK")
    provider = _provider()
    assert provider.search(destination="New York") == []
    assert provider.used_mock_fallback is False
    assert provider.last_result.status == ProviderStatus.UNAVAILABLE


def test_live_failure_raises_by_default(monkeypatch):
    monkeypatch.setenv(_MODE, "LIVE")
    provider = _provider()
    with pytest.raises(LiveEventSearchUnavailableError):
        provider.search(destination="New York", interests=["soccer"])
    assert provider.used_mock_fallback is False


def test_live_failure_can_use_labelled_curated_fallback(monkeypatch):
    monkeypatch.setenv(_MODE, "LIVE")
    monkeypatch.setenv(_FALLBACK, "true")
    provider = _provider()
    options = provider.search(destination="New York", interests=["soccer"])
    assert len(options) == 4
    assert provider.used_mock_fallback is True
    assert all(option["starts_at"] is None for option in options)


def test_generic_live_events_request_uses_broad_destination_date_search():
    assert _distinct_event_search_interests(
        ["major attractions", "live events"]
    ) == []
