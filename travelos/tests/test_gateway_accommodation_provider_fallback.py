"""
GatewayAccommodationProvider's T-039 additions: last_result tracking,
adults/children/rooms forwarding, and the LIVE_SANDBOX failure/fallback
policy — never mixing mock and live properties, an explicit error by
default, mock fallback only when enabled and clearly labelled.
"""

from __future__ import annotations

import pytest

from travelos.intelligence_gateway.discovery_adapters import (
    GatewayAccommodationProvider,
    LiveAccommodationSearchUnavailableError,
)
from travelos.intelligence_gateway.gateway import IntelligenceGateway
from travelos.intelligence_gateway.provider_registry import ProviderRegistry
from travelos.intelligence_gateway.provider_status import ProviderStatus

_MODE_VAR = "TRALVANA_ACCOMMODATION_PROVIDER_MODE"
_FALLBACK_VAR = "TRALVANA_ACCOMMODATION_MOCK_FALLBACK_ENABLED"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv(_MODE_VAR, raising=False)
    monkeypatch.delenv(_FALLBACK_VAR, raising=False)


def _empty_gateway() -> IntelligenceGateway:
    return IntelligenceGateway(registry=ProviderRegistry())


class TestLastResultTracking:
    def test_last_result_none_before_any_search(self):
        provider = GatewayAccommodationProvider(gateway=_empty_gateway())
        assert provider.last_result is None

    def test_last_result_populated_after_search(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "MOCK")
        provider = GatewayAccommodationProvider(gateway=_empty_gateway())
        provider.search(destination="Tokyo", check_in_date="2026-10-01", nights=2)
        assert provider.last_result is not None
        assert provider.last_result.status == ProviderStatus.UNAVAILABLE


class TestMockModeNeverRaises:
    def test_no_eligible_provider_in_mock_mode_returns_empty_list(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "MOCK")
        provider = GatewayAccommodationProvider(gateway=_empty_gateway())
        options = provider.search(destination="Tokyo", check_in_date="2026-10-01", nights=2)
        assert options == []
        assert provider.used_mock_fallback is False


class TestLiveSandboxFailureWithoutFallback:
    def test_raises_live_accommodation_search_unavailable_error(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        monkeypatch.setenv(_FALLBACK_VAR, "false")
        provider = GatewayAccommodationProvider(gateway=_empty_gateway())
        with pytest.raises(LiveAccommodationSearchUnavailableError):
            provider.search(destination="Tokyo", check_in_date="2026-10-01", nights=2)

    def test_used_mock_fallback_stays_false_on_raise(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        provider = GatewayAccommodationProvider(gateway=_empty_gateway())
        with pytest.raises(LiveAccommodationSearchUnavailableError):
            provider.search(destination="Tokyo", check_in_date="2026-10-01", nights=2)
        assert provider.used_mock_fallback is False


class TestLiveSandboxFailureWithFallbackEnabled:
    def test_falls_back_to_mock_data_instead_of_raising(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        monkeypatch.setenv(_FALLBACK_VAR, "true")
        provider = GatewayAccommodationProvider(gateway=_empty_gateway())
        options = provider.search(destination="Tokyo", check_in_date="2026-10-01", nights=2)
        assert len(options) > 0
        assert provider.used_mock_fallback is True

    def test_fallback_data_is_entirely_mock_never_mixed_with_live(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        monkeypatch.setenv(_FALLBACK_VAR, "true")
        provider = GatewayAccommodationProvider(gateway=_empty_gateway())
        options = provider.search(destination="Tokyo", check_in_date="2026-10-01", nights=2)
        for option in options:
            assert "_provider_source" not in option


class TestAdultsChildrenRoomsForwarding:
    def test_forwarded_to_mock_fallback_without_error(self, monkeypatch):
        # MockAccommodationProvider accepts and ignores these (T-039) —
        # this asserts the call succeeds with no TypeError, not that the
        # mock's own candidates change.
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        monkeypatch.setenv(_FALLBACK_VAR, "true")
        provider = GatewayAccommodationProvider(gateway=_empty_gateway())
        options = provider.search(
            destination="Tokyo", check_in_date="2026-10-01", nights=2, adults=3, children=2, rooms=2
        )
        assert len(options) > 0
