from __future__ import annotations

from pathlib import Path

import pytest

from travelos.intelligence_gateway.provider_registry import ProviderRegistry
from travelos.intelligence_gateway.provider_status import Capability
from travelos.live_providers.event_provider_bootstrap import (
    EventProviderMisconfiguredError,
    configure_event_provider,
)

_MODE = "TRALVANA_EVENT_PROVIDER_MODE"
_KEY = "TICKETMASTER_API_KEY"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv(_MODE, raising=False)
    monkeypatch.delenv(_KEY, raising=False)


def test_mock_mode_registers_no_live_event_provider(monkeypatch):
    monkeypatch.setenv(_MODE, "MOCK")
    registry = ProviderRegistry()
    configure_event_provider(registry)
    assert registry.get_providers(Capability.EVENTS) == []


def test_key_presence_alone_never_enables_live_calls(monkeypatch):
    monkeypatch.setenv(_KEY, "consumer-key-for-test")
    registry = ProviderRegistry()
    configure_event_provider(registry)
    assert registry.get_providers(Capability.EVENTS) == []


def test_live_mode_registers_ticketmaster(monkeypatch):
    monkeypatch.setenv(_MODE, "LIVE")
    monkeypatch.setenv(_KEY, "consumer-key-for-test")
    registry = ProviderRegistry()
    configure_event_provider(registry)
    names = [
        provider.provider_name
        for provider in registry.get_providers(Capability.EVENTS)
    ]
    assert names == ["ticketmaster_event_provider"]


def test_live_mode_registration_is_idempotent(monkeypatch):
    monkeypatch.setenv(_MODE, "LIVE")
    monkeypatch.setenv(_KEY, "consumer-key-for-test")
    registry = ProviderRegistry()
    configure_event_provider(registry)
    configure_event_provider(registry)
    assert len(registry.get_providers(Capability.EVENTS)) == 1


def test_live_mode_requires_key(monkeypatch):
    monkeypatch.setenv(_MODE, "LIVE")
    with pytest.raises(EventProviderMisconfiguredError) as exc_info:
        configure_event_provider(ProviderRegistry())
    assert "TICKETMASTER_API_KEY" in str(exc_info.value)


def test_windows_api_launcher_loads_repo_env_file():
    repo_root = Path(__file__).resolve().parents[2]
    launcher = (repo_root / "scripts" / "start-api.ps1").read_text(
        encoding="utf-8"
    )
    assert '$EnvFile = Join-Path $RepoRoot ".env"' in launcher
    assert '"--env-file", $EnvFile' in launcher
