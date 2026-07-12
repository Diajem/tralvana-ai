"""
BaseLiveProvider's execute() lifecycle — validate -> authenticate ->
build_request -> send_request -> parse_response -> ProviderResult, and
its standard HTTP-status-to-error mapping
(docs/LIVE_PROVIDER_FRAMEWORK.md). Never a real network call —
`ExampleFlightProvider` (the non-production template) is used
throughout, always with `FakeTransport`.
"""

from __future__ import annotations

import pytest

from travelos.intelligence_gateway.exceptions import (
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderValidationError,
)
from travelos.intelligence_gateway.provider_contract import ProviderRequest
from travelos.intelligence_gateway.provider_status import Capability, ProviderEnvironment, ProviderStatus
from travelos.live_providers.templates.example_flight_provider import ExampleFlightProvider
from travelos.live_providers.transport import FakeTransport

_ENV_VAR = "EXAMPLE_AIRLINE_API_KEY"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv(_ENV_VAR, raising=False)


def _req(**params) -> ProviderRequest:
    return ProviderRequest(
        capability=Capability.FLIGHTS, operation="search",
        params={"origin": "LON", "destination": "Tokyo", "departure_date": "2026-10-01", **params},
    )


class TestExecutionLifecycle:
    def test_successful_execution_returns_a_provider_result(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        provider = ExampleFlightProvider()
        result = provider.execute(_req())
        assert result.status == ProviderStatus.AVAILABLE
        assert result.provider_name == "example_flight_provider_template"
        assert result.capability == Capability.FLIGHTS

    def test_result_carries_latency_and_request_id(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        provider = ExampleFlightProvider()
        result = provider.execute(_req())
        assert result.latency_ms >= 0
        assert result.request_id != ""
        assert result.retrieved_at != ""

    def test_unsupported_operation_raises_validation_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        provider = ExampleFlightProvider()
        bad_request = ProviderRequest(capability=Capability.WEATHER, operation="search", params={})
        with pytest.raises(ProviderValidationError):
            provider.execute(bad_request)


class TestSecretAbsence:
    def test_execute_raises_configuration_error_when_secret_unset(self):
        provider = ExampleFlightProvider()
        with pytest.raises(ProviderConfigurationError):
            provider.execute(_req())

    def test_transport_never_called_when_secret_unset(self):
        transport = FakeTransport()
        provider = ExampleFlightProvider(transport=transport)
        with pytest.raises(ProviderConfigurationError):
            provider.execute(_req())
        assert transport.sent_requests == []


class TestRequestMapping:
    def test_build_request_maps_internal_params_to_transport_request(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        transport = FakeTransport.always_returning(status_code=200, body={"request_id": "x", "flights": []})
        provider = ExampleFlightProvider(transport=transport)
        provider.execute(_req(origin="LHR", destination="Paris", departure_date="2026-12-25"))

        sent = transport.sent_requests[0]
        assert sent.method == "GET"
        assert sent.query_params["origin"] == "LHR"
        assert sent.query_params["destination"] == "Paris"
        assert sent.query_params["date"] == "2026-12-25"

    def test_auth_headers_merged_into_the_transport_request(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "my-test-key-value")
        transport = FakeTransport.always_returning(status_code=200, body={"request_id": "x", "flights": []})
        provider = ExampleFlightProvider(transport=transport)
        provider.execute(_req())
        assert transport.sent_requests[0].headers["X-API-Key"] == "my-test-key-value"

    def test_url_never_points_at_a_resolvable_host(self, monkeypatch):
        # .invalid is reserved by RFC 2606 to never resolve.
        monkeypatch.setenv(_ENV_VAR, "test-key")
        transport = FakeTransport.always_returning(status_code=200, body={"request_id": "x", "flights": []})
        provider = ExampleFlightProvider(transport=transport)
        provider.execute(_req())
        assert transport.sent_requests[0].url.endswith(".invalid/v1/flights/search")


class TestResponseMapping:
    def test_successful_body_maps_to_result_data(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        transport = FakeTransport.always_returning(
            status_code=200, body={"request_id": "abc-123", "flights": [{"airline": "Test Air", "price": 100}]},
        )
        provider = ExampleFlightProvider(transport=transport)
        result = provider.execute(_req())
        assert result.data == [{"airline": "Test Air", "price": 100}]
        assert result.source_metadata["provider_request_id"] == "abc-123"

    def test_malformed_response_raises_response_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        transport = FakeTransport.always_returning(status_code=200, body={"unexpected": "shape"})
        provider = ExampleFlightProvider(transport=transport)
        with pytest.raises(ProviderResponseError):
            provider.execute(_req())

    def test_non_dict_body_raises_response_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        transport = FakeTransport.always_returning(status_code=200, body="not a dict")
        provider = ExampleFlightProvider(transport=transport)
        with pytest.raises(ProviderResponseError):
            provider.execute(_req())


class TestStandardErrorMapping:
    def test_401_maps_to_authentication_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        transport = FakeTransport.always_returning(status_code=401)
        provider = ExampleFlightProvider(transport=transport)
        with pytest.raises(ProviderAuthenticationError):
            provider.execute(_req())

    def test_403_maps_to_authentication_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        transport = FakeTransport.always_returning(status_code=403)
        provider = ExampleFlightProvider(transport=transport)
        with pytest.raises(ProviderAuthenticationError):
            provider.execute(_req())

    def test_429_maps_to_rate_limit_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        transport = FakeTransport.always_returning(status_code=429)
        provider = ExampleFlightProvider(transport=transport)
        with pytest.raises(ProviderRateLimitError):
            provider.execute(_req())

    def test_408_maps_to_timeout_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        transport = FakeTransport.always_returning(status_code=408)
        provider = ExampleFlightProvider(transport=transport)
        with pytest.raises(ProviderTimeoutError):
            provider.execute(_req())

    def test_500_maps_to_unavailable_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        transport = FakeTransport.always_returning(status_code=500)
        provider = ExampleFlightProvider(transport=transport)
        with pytest.raises(ProviderUnavailableError):
            provider.execute(_req())

    def test_503_maps_to_unavailable_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        transport = FakeTransport.always_returning(status_code=503)
        provider = ExampleFlightProvider(transport=transport)
        with pytest.raises(ProviderUnavailableError):
            provider.execute(_req())

    def test_unmapped_4xx_maps_to_response_error(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        transport = FakeTransport.always_returning(status_code=418)
        provider = ExampleFlightProvider(transport=transport)
        with pytest.raises(ProviderResponseError):
            provider.execute(_req())

    def test_transport_raising_a_generic_exception_is_wrapped_as_unavailable(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")

        def _boom(request):
            raise RuntimeError("connection reset")

        transport = FakeTransport(responder=_boom)
        provider = ExampleFlightProvider(transport=transport)
        with pytest.raises(ProviderUnavailableError):
            provider.execute(_req())


class TestHealthChecks:
    def test_unconfigured_provider_is_misconfigured(self):
        provider = ExampleFlightProvider()
        assert provider.health_check() == ProviderStatus.MISCONFIGURED

    def test_configured_provider_is_available(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        provider = ExampleFlightProvider()
        assert provider.health_check() == ProviderStatus.AVAILABLE

    def test_detailed_health_result_has_required_fields(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "test-key")
        provider = ExampleFlightProvider()
        detailed = provider.health_check_detailed()
        assert detailed.provider_name == "example_flight_provider_template"
        assert detailed.capability == Capability.FLIGHTS
        assert detailed.environment == ProviderEnvironment.SANDBOX
        assert detailed.status == ProviderStatus.AVAILABLE
        assert detailed.checked_at != ""
        assert detailed.latency_ms >= 0
        assert detailed.metadata["auth_configured"] is True

    def test_detailed_health_never_includes_the_secret_value(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "super-secret-should-not-appear")
        provider = ExampleFlightProvider()
        detailed = provider.health_check_detailed()
        serialized = str(detailed)
        assert "super-secret-should-not-appear" not in serialized
