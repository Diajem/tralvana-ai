"""
GatewayFlightProvider's T-038 additions: last_result tracking, and the
LIVE_SANDBOX failure/fallback policy — never mixing mock and live
offers, an explicit error by default, mock fallback only when enabled
and clearly labelled via used_mock_fallback.
"""

from __future__ import annotations

import pytest

from travelos.intelligence_gateway.discovery_adapters import (
    GatewayFlightProvider,
    LiveFlightSearchUnavailableError,
)
from travelos.intelligence_gateway.gateway import IntelligenceGateway
from travelos.intelligence_gateway.provider_registry import ProviderRegistry
from travelos.intelligence_gateway.provider_status import ProviderStatus

_MODE_VAR = "TRALVANA_FLIGHT_PROVIDER_MODE"
_FALLBACK_VAR = "TRALVANA_FLIGHT_MOCK_FALLBACK_ENABLED"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv(_MODE_VAR, raising=False)
    monkeypatch.delenv(_FALLBACK_VAR, raising=False)


def _empty_gateway() -> IntelligenceGateway:
    # No provider registered at all for FLIGHTS — the simplest way to
    # force an UNAVAILABLE ProviderResult deterministically.
    return IntelligenceGateway(registry=ProviderRegistry())


class TestLastResultTracking:
    def test_last_result_none_before_any_search(self):
        provider = GatewayFlightProvider(gateway=_empty_gateway())
        assert provider.last_result is None

    def test_last_result_populated_after_search(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "MOCK")
        provider = GatewayFlightProvider(gateway=_empty_gateway())
        provider.search(origin="LON", destination="NYC", departure_date="2026-10-01", return_date=None, cabin_class="economy")
        assert provider.last_result is not None
        assert provider.last_result.status == ProviderStatus.UNAVAILABLE


class TestMockModeNeverRaises:
    def test_no_eligible_provider_in_mock_mode_returns_empty_list(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "MOCK")
        provider = GatewayFlightProvider(gateway=_empty_gateway())
        options = provider.search(origin="LON", destination="NYC", departure_date="2026-10-01", return_date=None, cabin_class="economy")
        assert options == []
        assert provider.used_mock_fallback is False


class TestLiveSandboxFailureWithoutFallback:
    def test_raises_live_flight_search_unavailable_error(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        monkeypatch.setenv(_FALLBACK_VAR, "false")
        provider = GatewayFlightProvider(gateway=_empty_gateway())
        with pytest.raises(LiveFlightSearchUnavailableError):
            provider.search(origin="LON", destination="NYC", departure_date="2026-10-01", return_date=None, cabin_class="economy")

    def test_used_mock_fallback_stays_false_on_raise(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        provider = GatewayFlightProvider(gateway=_empty_gateway())
        with pytest.raises(LiveFlightSearchUnavailableError):
            provider.search(origin="LON", destination="NYC", departure_date="2026-10-01", return_date=None, cabin_class="economy")
        assert provider.used_mock_fallback is False


class TestLiveSandboxFailureWithFallbackEnabled:
    def test_falls_back_to_mock_data_instead_of_raising(self, monkeypatch):
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        monkeypatch.setenv(_FALLBACK_VAR, "true")
        provider = GatewayFlightProvider(gateway=_empty_gateway())
        options = provider.search(origin="LON", destination="NYC", departure_date="2026-10-01", return_date=None, cabin_class="economy")
        assert len(options) > 0
        assert provider.used_mock_fallback is True

    def test_fallback_data_is_entirely_mock_never_mixed_with_live(self, monkeypatch):
        # With no live provider registered at all, every returned option
        # must have come from MockFlightProvider — there is nothing live
        # to blend in, and the fallback path never attempts to.
        monkeypatch.setenv(_MODE_VAR, "LIVE_SANDBOX")
        monkeypatch.setenv(_FALLBACK_VAR, "true")
        provider = GatewayFlightProvider(gateway=_empty_gateway())
        options = provider.search(origin="LON", destination="NYC", departure_date="2026-10-01", return_date=None, cabin_class="economy")
        for option in options:
            assert "_provider_offer_id" not in option
