"""
NON-PRODUCTION TEMPLATE — demonstrates how to build a concrete live
provider on `BaseLiveProvider` (docs/LIVE_PROVIDER_ADAPTER_GUIDE.md).

`ExampleFlightProvider` is not a real vendor and never makes a real
network call — it defaults to `FakeTransport`, and its request URL uses
the `.invalid` TLD (RFC 2606 — guaranteed never to resolve) as a second,
belt-and-braces guarantee even if a real `Transport` were substituted by
mistake. Copy this file's shape when building a real adapter (e.g. for
Duffel or Amadeus); do not import or register this class anywhere
outside tests/examples.
"""

from __future__ import annotations

from travelos.intelligence_gateway.exceptions import ProviderResponseError
from travelos.intelligence_gateway.provider_contract import ProviderRequest
from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_status import Capability, ProviderEnvironment, ProviderStatus
from travelos.intelligence_gateway.secret_reference import SecretReference
from travelos.live_providers.auth.api_key_auth import ApiKeyAuthStrategy
from travelos.live_providers.base_live_provider import BaseLiveProvider
from travelos.live_providers.transport import FakeTransport, Transport, TransportRequest, TransportResponse


class ExampleFlightProvider(BaseLiveProvider):
    """NON-PRODUCTION TEMPLATE. Demonstrates the full BaseLiveProvider
    lifecycle — authentication, request mapping, transport execution,
    response parsing, error mapping, health check — entirely against
    FakeTransport."""

    def __init__(
        self,
        transport: Transport | None = None,
        api_key_env_var: str = "EXAMPLE_AIRLINE_API_KEY",
    ) -> None:
        super().__init__(
            provider_name="example_flight_provider_template",
            capability=Capability.FLIGHTS,
            environment=ProviderEnvironment.SANDBOX,
            transport=transport or FakeTransport(responder=self._fake_vendor_response),
            auth=ApiKeyAuthStrategy(secret=SecretReference(env_var=api_key_env_var, required=True)),
            priority=200,  # a template should never outrank a real provider by default
        )

    def build_request(self, request: ProviderRequest) -> TransportRequest:
        """Internal ProviderRequest -> vendor-shaped TransportRequest. A
        real adapter's request-mapping logic lives here, and only here —
        never in a shared domain model."""
        return TransportRequest(
            method="GET",
            url="https://example-airline.invalid/v1/flights/search",
            query_params={
                "origin": request.params.get("origin", ""),
                "destination": request.params.get("destination", ""),
                "date": request.params.get("departure_date", ""),
            },
            timeout_seconds=10.0,
        )

    def parse_response(self, response: TransportResponse) -> ProviderResult:
        """Vendor-shaped TransportResponse -> ProviderResult."""
        body = response.body
        if not isinstance(body, dict) or "flights" not in body:
            raise ProviderResponseError(
                f"{self.provider_name}: response missing expected 'flights' field"
            )
        return ProviderResult(
            provider_name=self.provider_name,
            capability=self.capability,
            status=ProviderStatus.AVAILABLE,
            data=body["flights"],
            confidence=0.9,
            source_metadata={"provider_request_id": body.get("request_id", "")},
        )

    def map_error(self, error: Exception) -> Exception:
        """A real adapter would inspect a vendor-specific error body here
        (e.g. `{"error": {"code": ..., "message": ...}}`) and translate it
        into the right standard error type. This template has no real
        vendor error shape to translate, so it defers to the base
        default (docs/PROVIDER_ERROR_MODEL.md)."""
        return super().map_error(error)

    @staticmethod
    def _fake_vendor_response(request: TransportRequest) -> TransportResponse:
        """The default FakeTransport responder — simulates a plausible
        vendor payload entirely in-memory, no network involved."""
        return TransportResponse(
            status_code=200,
            body={
                "request_id": "example-req-123",
                "flights": [{"airline": "Example Air", "price": 450, "currency": "USD"}],
            },
        )
