"""Manual search-only verification. Never creates orders, bookings or payments."""

import argparse
from datetime import date, timedelta
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from ai.discovery.accommodation.accommodation_intelligence import AccommodationIntelligence  # noqa: E402
from ai.discovery.flights.flight_intelligence import FlightIntelligence  # noqa: E402
from travelos.intelligence_gateway.discovery_adapters import GatewayAccommodationProvider, GatewayFlightProvider  # noqa: E402
from travelos.intelligence_gateway.gateway import IntelligenceGateway  # noqa: E402
from travelos.intelligence_gateway.provider_registry import ProviderRegistry  # noqa: E402
from travelos.intelligence_gateway.provider_status import ProviderEnvironment  # noqa: E402
from travelos.live_providers.adapters.duffel_flight_provider import register_duffel_flight_provider  # noqa: E402
from travelos.live_providers.adapters.duffel_stays_provider import register_duffel_stays_provider  # noqa: E402
from travelos.live_providers.duffel_credentials import duffel_token_variable  # noqa: E402
from travelos.live_providers.httpx_transport import HttpxTransport  # noqa: E402


class SearchTransport(HttpxTransport):
    def __init__(self):
        super().__init__()
        self.statuses = []
        self.error_codes = []

    def send(self, request):
        if not (request.url.endswith("/air/offer_requests")
                or request.url.endswith("/places/suggestions")
                or request.url.endswith("/stays/search")):
            raise ValueError("Only search endpoints are allowed by this verifier")
        result = super().send(request)
        self.statuses.append(result.status_code)
        if result.status_code >= 400 and isinstance(result.body, dict):
            self.error_codes.extend(str(e.get("code", "")) for e in result.body.get("errors", []))
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product", choices=["flights", "stays"], required=True)
    args = parser.parse_args()
    token_var = duffel_token_variable(args.product, live=True)
    registry = ProviderRegistry()
    transport = SearchTransport()
    register = register_duffel_flight_provider if args.product == "flights" else register_duffel_stays_provider
    register(transport=transport, registry=registry, token_env_var=token_var,
             environment=ProviderEnvironment.PRODUCTION)
    gateway = IntelligenceGateway(registry=registry, environment=ProviderEnvironment.PRODUCTION)
    future = (date.today() + timedelta(days=30)).isoformat()
    report = {"product": args.product, "booking_attempted": False}
    try:
        if args.product == "flights":
            result = FlightIntelligence(provider=GatewayFlightProvider(gateway)).recommend(
                origin="LHR", destination="JFK", departure_date=future, return_date=None, adults=2,
            )
            options = result["flight_options"]
        else:
            result = AccommodationIntelligence(provider=GatewayAccommodationProvider(gateway)).recommend(
                destination="London", check_in_date=future, nights=3, adults=2,
                children=1, child_ages=[7], rooms=1,
            )
            options = result["accommodation_options"]
        report.update(data_source=result["data_source"], count=len(options), status=result["provider_status"])
        if options:
            first = options[0]
            report["sample"] = {key: first[key] for key in
                                ("airline", "property_name", "currency", "estimated_price", "total_price")
                                if key in first}
    except Exception as exc:
        report.update(status="ERROR", error_type=type(exc).__name__)
    finally:
        transport.close()
    report.update(http_statuses=transport.statuses, provider_error_codes=transport.error_codes)
    print(json.dumps(report))
    return 0 if report["status"] == "AVAILABLE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
