"""
Manual live verification for the Duffel Stays sandbox integration (T-039).

    python scripts/verify_duffel_stays_live_sandbox.py

Reads DUFFEL_API_TOKEN from the repo root .env (never prints it), then
runs exactly one accommodation search through the real product
architecture:

    AccommodationIntelligence
      -> GatewayAccommodationProvider -> IntelligenceGateway
        -> DuffelStaysProvider -> HttpxTransport -> Duffel SANDBOX API
      -> normalised accommodation-option dicts -> AccommodationScorer
      -> AccommodationReasoner -> ranked results

Never run as part of pytest/CI — see docs/DUFFEL_STAYS_INTEGRATION.md.
Reports only safe diagnostics: HTTP status, provider status, request
success, raw property/rate count, normalised count, ranked count, and
the request id. The token and the full raw payload are never printed.

**Known outcome as of T-039**: the DUFFEL_API_TOKEN already configured
for Flights sandbox testing does NOT have Stays access — running this
script reports a clean HTTP 403 with a clear access-not-enabled message
rather than a successful search. That is the correct, expected result
until Stays access is separately requested for this Duffel account
(docs/DUFFEL_STAYS_INTEGRATION.md's Access Requirement section) — this
script still runs to produce that evidence, not to succeed unconditionally.
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=_REPO_ROOT / ".env", override=True)

sys.path.insert(0, str(_REPO_ROOT))

from ai.discovery.accommodation.accommodation_intelligence import AccommodationIntelligence  # noqa: E402
from travelos.intelligence_gateway.discovery_adapters import GatewayAccommodationProvider  # noqa: E402
from travelos.intelligence_gateway.gateway import IntelligenceGateway  # noqa: E402
from travelos.intelligence_gateway.provider_registry import ProviderRegistry  # noqa: E402
from travelos.intelligence_gateway.provider_status import ProviderEnvironment  # noqa: E402
from travelos.intelligence_gateway.secret_reference import SecretReference  # noqa: E402
from travelos.live_providers.adapters.duffel_stays_provider import register_duffel_stays_provider  # noqa: E402
from travelos.live_providers.httpx_transport import HttpxTransport  # noqa: E402
from travelos.live_providers.transport import TransportRequest, TransportResponse  # noqa: E402


class _StatusCapturingTransport(HttpxTransport):
    """Records the raw HTTP status code of the *last* request (the
    search call, since it's sent after the Places lookup) — never the
    token, never the full response body."""

    last_status_code: int | None = None
    last_body_preview: str | None = None

    def send(self, request: TransportRequest) -> TransportResponse:
        response = super().send(request)
        self.last_status_code = response.status_code
        # Safe preview only — Duffel's access-not-enabled error is a
        # short plain-text message, not a payload with property data.
        if isinstance(response.body, str):
            self.last_body_preview = response.body[:200]
        return response


def main() -> int:
    token = SecretReference(env_var="DUFFEL_API_TOKEN", required=True, description="Duffel sandbox token")
    if not token.is_present():
        print("DUFFEL_API_TOKEN is not set — nothing to verify. See docs/DUFFEL_STAYS_INTEGRATION.md.")
        return 1

    registry = ProviderRegistry()
    transport = _StatusCapturingTransport()
    register_duffel_stays_provider(transport=transport, registry=registry, environment=ProviderEnvironment.SANDBOX)
    gateway = IntelligenceGateway(registry=registry, environment=ProviderEnvironment.SANDBOX)
    gateway_provider = GatewayAccommodationProvider(gateway=gateway)
    engine = AccommodationIntelligence(provider=gateway_provider)

    try:
        result = engine.recommend(
            destination="Tokyo",
            check_in_date="2026-09-01",
            nights=2,
            adults=1,
        )
    except Exception as exc:  # noqa: BLE001 — diagnostic script, not library code
        print("http_status_code:", transport.last_status_code)
        print("provider_status: error")
        print("request_success: False")
        print("error_type:", type(exc).__name__)
        if transport.last_body_preview:
            print("response_preview (safe, no payload data):", transport.last_body_preview)
        return 1
    finally:
        transport.close()

    print("http_status_code:", transport.last_status_code)
    print("provider_status:", result["provider_status"])
    print("request_success:", result["data_source"] == "DUFFEL_STAYS_SANDBOX")
    print("data_source:", result["data_source"])
    print("raw_results_count:", result["raw_results_count"])
    print("normalised_results_count:", result["normalised_results_count"])
    print("ranked_results_count:", result["ranked_results_count"])
    print("request_id:", result["request_id"])
    if transport.last_body_preview:
        print("response_preview (safe, no payload data):", transport.last_body_preview)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
