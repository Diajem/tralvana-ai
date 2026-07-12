"""
Proves BaseLiveProvider.execute() actually records into a
ProviderMetricsTracker on every call — success, failure, and rate-limit
outcomes alike — not just that the tracker class works in isolation
(see test_provider_metrics.py for that).
"""

from __future__ import annotations

import pytest

from travelos.intelligence_gateway.exceptions import ProviderRateLimitError, ProviderUnavailableError
from travelos.intelligence_gateway.provider_contract import ProviderRequest
from travelos.intelligence_gateway.provider_status import Capability
from travelos.live_providers.metrics.provider_metrics import ProviderMetricsTracker
from travelos.live_providers.templates.example_flight_provider import ExampleFlightProvider
from travelos.live_providers.transport import FakeTransport

_ENV_VAR = "EXAMPLE_AIRLINE_API_KEY"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv(_ENV_VAR, raising=False)


def _req() -> ProviderRequest:
    return ProviderRequest(
        capability=Capability.FLIGHTS, operation="search",
        params={"origin": "LON", "destination": "Tokyo", "departure_date": "2026-10-01"},
    )


class TestMetricsRecordedByExecute:
    def test_successful_execution_records_a_success(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        metrics = ProviderMetricsTracker()
        transport = FakeTransport.always_returning(status_code=200, body={"request_id": "x", "flights": []})
        provider = ExampleFlightProvider(transport=transport)
        provider._metrics = metrics

        provider.execute(_req())

        snap = metrics.snapshot_for(provider.provider_name)
        assert snap.success_count == 1
        assert snap.failure_count == 0

    def test_failed_execution_records_a_failure(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        metrics = ProviderMetricsTracker()
        transport = FakeTransport.always_returning(status_code=500)
        provider = ExampleFlightProvider(transport=transport)
        provider._metrics = metrics

        with pytest.raises(ProviderUnavailableError):
            provider.execute(_req())

        snap = metrics.snapshot_for(provider.provider_name)
        assert snap.failure_count == 1
        assert snap.success_count == 0

    def test_rate_limited_execution_records_a_rate_limit_not_a_failure(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        metrics = ProviderMetricsTracker()
        transport = FakeTransport.always_returning(status_code=429)
        provider = ExampleFlightProvider(transport=transport)
        provider._metrics = metrics

        with pytest.raises(ProviderRateLimitError):
            provider.execute(_req())

        snap = metrics.snapshot_for(provider.provider_name)
        assert snap.rate_limited_count == 1
        assert snap.failure_count == 0

    def test_latency_recorded_on_success(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        metrics = ProviderMetricsTracker()
        transport = FakeTransport.always_returning(status_code=200, body={"request_id": "x", "flights": []})
        provider = ExampleFlightProvider(transport=transport)
        provider._metrics = metrics

        provider.execute(_req())

        assert metrics.snapshot_for(provider.provider_name).last_latency_ms >= 0
