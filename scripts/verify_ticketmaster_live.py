"""Run one safe live Ticketmaster Discovery search through Event Intelligence.

Usage from the repository root:

    .venv\\Scripts\\python.exe scripts\\verify_ticketmaster_live.py

The script reads TICKETMASTER_API_KEY from .env and never prints the key,
request query string, headers, or raw provider response.
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=_REPO_ROOT / ".env", override=True)
sys.path.insert(0, str(_REPO_ROOT))

from ai.discovery.events.event_intelligence import EventIntelligence  # noqa: E402
from travelos.intelligence_gateway.discovery_adapters import (  # noqa: E402
    GatewayEventProvider,
)
from travelos.intelligence_gateway.gateway import IntelligenceGateway  # noqa: E402
from travelos.intelligence_gateway.provider_registry import ProviderRegistry  # noqa: E402
from travelos.intelligence_gateway.provider_status import (  # noqa: E402
    ProviderEnvironment,
)
from travelos.intelligence_gateway.secret_reference import SecretReference  # noqa: E402
from travelos.live_providers.adapters.ticketmaster_event_provider import (  # noqa: E402
    register_ticketmaster_event_provider,
)
from travelos.live_providers.httpx_transport import HttpxTransport  # noqa: E402
from travelos.live_providers.transport import (  # noqa: E402
    TransportRequest,
    TransportResponse,
)


class _StatusCapturingTransport(HttpxTransport):
    last_status_code: int | None = None

    def send(self, request: TransportRequest) -> TransportResponse:
        response = super().send(request)
        self.last_status_code = response.status_code
        return response


def main() -> int:
    key = SecretReference(
        env_var="TICKETMASTER_API_KEY",
        required=True,
        description="Ticketmaster Discovery API consumer key",
    )
    if not key.is_present():
        print(
            "TICKETMASTER_API_KEY is not set — nothing to verify. "
            "See docs/LIVE_EVENT_SEARCH.md."
        )
        return 1

    registry = ProviderRegistry()
    transport = _StatusCapturingTransport()
    register_ticketmaster_event_provider(transport=transport, registry=registry)
    gateway = IntelligenceGateway(
        registry=registry,
        environment=ProviderEnvironment.PRODUCTION,
    )
    gateway_provider = GatewayEventProvider(gateway=gateway)
    engine = EventIntelligence(provider=gateway_provider)

    try:
        result = engine.recommend(
            destination="New York",
            start_date="2026-08-07",
            end_date="2026-08-22",
            interests=["fashion", "soccer"],
        )
    except Exception as exc:  # noqa: BLE001 — operator diagnostic only
        print("http_status_code:", transport.last_status_code)
        print("provider_status: error")
        print("error_type:", type(exc).__name__)
        return 1
    finally:
        transport.close()

    provider_result = gateway_provider.last_result
    raw_count = (
        provider_result.source_metadata.get("raw_event_count", 0)
        if provider_result
        else 0
    )
    print("http_status_code:", transport.last_status_code)
    print("provider_status:", result["provider_status"])
    print("data_source:", result["data_source"])
    print("raw_event_count:", raw_count)
    print("ranked_event_count:", len(result["event_options"]))
    print(
        "excluded_outside_travel_dates:",
        result["filter_summary"]["excluded_outside_travel_dates"],
    )
    print(
        "excluded_as_irrelevant:",
        result["filter_summary"]["excluded_as_irrelevant"],
    )
    print("request_id:", provider_result.request_id if provider_result else "")
    for option in result["event_options"][:3]:
        print(
            "event:",
            option["name"],
            "| starts_at:",
            option["starts_at"],
            "| status:",
            option["availability_status"],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
