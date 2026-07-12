"""
Manual live verification for the Duffel sandbox integration (T-038).

    python scripts/verify_duffel_live_sandbox.py

Reads DUFFEL_API_TOKEN from the repo root .env (never prints it), then
runs exactly one flight search through the real product architecture:

    FlightIntelligence (Flight Intelligence Service)
      -> GatewayFlightProvider -> IntelligenceGateway
        -> DuffelFlightProvider -> HttpxTransport -> Duffel SANDBOX API
      -> normalised flight-option dicts -> FlightScorer -> FlightReasoner
      -> ranked results

Never run as part of pytest/CI — see docs/DUFFEL_SANDBOX_OPERATIONS.md.
Reports only safe diagnostics: HTTP outcome, provider status, raw offer
count, normalised count, ranked count, and the request id. The token,
request headers, and full response payload are never printed.
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=_REPO_ROOT / ".env", override=True)

sys.path.insert(0, str(_REPO_ROOT))

from ai.discovery.flights.flight_intelligence import FlightIntelligence  # noqa: E402
from travelos.intelligence_gateway.discovery_adapters import GatewayFlightProvider  # noqa: E402
from travelos.intelligence_gateway.gateway import IntelligenceGateway  # noqa: E402
from travelos.intelligence_gateway.provider_registry import ProviderRegistry  # noqa: E402
from travelos.intelligence_gateway.provider_status import ProviderEnvironment  # noqa: E402
from travelos.intelligence_gateway.secret_reference import SecretReference  # noqa: E402
from travelos.live_providers.adapters.duffel_flight_provider import (  # noqa: E402
    register_duffel_flight_provider,
)
from travelos.live_providers.httpx_transport import HttpxTransport  # noqa: E402
from travelos.live_providers.transport import TransportRequest, TransportResponse  # noqa: E402


class _StatusCapturingTransport(HttpxTransport):
    """Records the raw HTTP status code only — ProviderResult itself
    carries the abstract ProviderStatus enum, not the wire-level code."""

    last_status_code: int | None = None

    def send(self, request: TransportRequest) -> TransportResponse:
        response = super().send(request)
        self.last_status_code = response.status_code
        return response


def main() -> int:
    token = SecretReference(env_var="DUFFEL_API_TOKEN", required=True, description="Duffel sandbox token")
    if not token.is_present():
        print("DUFFEL_API_TOKEN is not set — nothing to verify. See docs/DUFFEL_SANDBOX_OPERATIONS.md.")
        return 1

    registry = ProviderRegistry()
    transport = _StatusCapturingTransport()
    register_duffel_flight_provider(transport=transport, registry=registry, environment=ProviderEnvironment.SANDBOX)
    gateway = IntelligenceGateway(registry=registry, environment=ProviderEnvironment.SANDBOX)
    gateway_provider = GatewayFlightProvider(gateway=gateway)
    engine = FlightIntelligence(provider=gateway_provider)

    try:
        result = engine.recommend(
            origin="LHR",
            destination="JFK",
            departure_date="2026-08-15",
            return_date=None,
            cabin_class="economy",
        )
    except Exception as exc:  # noqa: BLE001 — diagnostic script, not library code
        print("http_status_code:", transport.last_status_code)
        print("provider_status: error")
        print("error_type:", type(exc).__name__)
        return 1
    finally:
        transport.close()

    raw_offer_count = 0
    if gateway_provider.last_result is not None:
        raw_offer_count = gateway_provider.last_result.source_metadata.get(
            "raw_offer_count", len(gateway_provider.last_result.data or [])
        )

    print("http_status_code:", transport.last_status_code)
    print("provider_status:", result["provider_status"])
    print("data_source:", result["data_source"])
    print("raw_offer_count:", raw_offer_count)
    print("normalised_offer_count:", result["results_count"])
    print("ranked_offer_count:", len(result["flight_options"]))
    print("request_id:", result["request_id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
