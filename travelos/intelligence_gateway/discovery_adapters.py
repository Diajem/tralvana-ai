"""
Discovery integration — the smallest safe wiring that proves the pattern
(docs/INTELLIGENCE_GATEWAY.md's Discovery Integration section).

Two layers, kept deliberately separate:

1. `_Mock*GatewayProvider` — the gateway-contract wrapper (`Provider`)
   registered in `provider_registry`. It delegates every call straight
   to the existing `Mock*Provider` class already used by each Discovery
   module (`ai/discovery/*/mock_*_provider.py`) — no internal logic is
   rewritten or duplicated (docs/PROVIDER_CONTRACT.md).

2. `Gateway*Provider` — a drop-in replacement for the plain
   `Mock*Provider`, implementing the *exact same* method signature each
   Discovery module's `*Intelligence` class already expects from its
   `provider` constructor argument. Internally it calls
   `IntelligenceGateway.execute()` instead of the mock class directly,
   so caching/retry/failover/observability apply, while every caller
   (`FlightIntelligence`, `AccommodationIntelligence`,
   `WeatherIntelligence`) is completely unaware anything changed.

Only these three capabilities are wired here — see
docs/INTELLIGENCE_GATEWAY.md's "Deferred Integrations" section for why
Destinations/Budget/Visa/Maps/Currency/Events are not (this task is
infrastructure-only; T-025's own instructions ask for the smallest safe
integration that proves the pattern, not a rewrite of every module).
"""

from __future__ import annotations

from typing import Any

from travelos.intelligence_gateway.gateway import IntelligenceGateway, intelligence_gateway
from travelos.intelligence_gateway.provider_contract import Provider, ProviderRequest
from travelos.intelligence_gateway.provider_registry import ProviderRegistry, provider_registry
from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_status import Capability, ProviderStatus

# ---------------------------------------------------------------------------
# Layer 1 — gateway-contract wrappers around the existing mock providers.
# ---------------------------------------------------------------------------


class _MockFlightGatewayProvider(Provider):
    def __init__(self) -> None:
        from ai.discovery.flights.flight_intelligence import MockFlightProvider
        self._provider = MockFlightProvider()

    @property
    def provider_name(self) -> str:
        return "mock_flight_provider"

    @property
    def capability(self) -> Capability:
        return Capability.FLIGHTS

    @property
    def priority(self) -> int:
        return 10

    @property
    def metadata(self) -> dict[str, Any]:
        return {"description": "Deterministic mock flight inventory — no live airline data."}

    def execute(self, request: ProviderRequest) -> ProviderResult:
        options = self._provider.search(**request.params)
        return ProviderResult(
            provider_name=self.provider_name, capability=self.capability,
            status=ProviderStatus.AVAILABLE, data=options, confidence=1.0,
            source_metadata={"mock": True},
        )


class _MockAccommodationGatewayProvider(Provider):
    def __init__(self) -> None:
        from ai.discovery.accommodation.mock_accommodation_provider import MockAccommodationProvider
        self._provider = MockAccommodationProvider()

    @property
    def provider_name(self) -> str:
        return "mock_accommodation_provider"

    @property
    def capability(self) -> Capability:
        return Capability.ACCOMMODATION

    @property
    def priority(self) -> int:
        return 10

    @property
    def metadata(self) -> dict[str, Any]:
        return {"description": "Deterministic mock accommodation inventory — no live booking data."}

    def execute(self, request: ProviderRequest) -> ProviderResult:
        options = self._provider.search(**request.params)
        return ProviderResult(
            provider_name=self.provider_name, capability=self.capability,
            status=ProviderStatus.AVAILABLE, data=options, confidence=1.0,
            source_metadata={"mock": True},
        )


class _MockWeatherGatewayProvider(Provider):
    _OPERATIONS = ("month", "year", "known_destinations")

    def __init__(self) -> None:
        from ai.discovery.weather.mock_weather_provider import MockWeatherProvider
        self._provider = MockWeatherProvider()

    @property
    def provider_name(self) -> str:
        return "mock_weather_provider"

    @property
    def capability(self) -> Capability:
        return Capability.WEATHER

    @property
    def priority(self) -> int:
        return 10

    @property
    def metadata(self) -> dict[str, Any]:
        return {"description": "Deterministic mock climate profiles — not a forecast."}

    def supports(self, request: ProviderRequest) -> bool:
        return request.capability == self.capability and request.operation in self._OPERATIONS

    def execute(self, request: ProviderRequest) -> ProviderResult:
        if request.operation == "month":
            data = self._provider.month(**request.params)
        elif request.operation == "year":
            data = self._provider.year(**request.params)
        else:
            data = self._provider.known_destinations()
        return ProviderResult(
            provider_name=self.provider_name, capability=self.capability,
            status=ProviderStatus.AVAILABLE, data=data, confidence=1.0,
            source_metadata={"mock": True},
        )


def register_default_providers(registry: ProviderRegistry | None = None) -> None:
    """Idempotent-in-intent — call once at import time (bottom of this
    module) to make the three mock providers accessible through the
    gateway. Tests that need a clean registry use their own
    ProviderRegistry instance instead of calling this again."""
    target = registry or provider_registry
    target.register(_MockFlightGatewayProvider())
    target.register(_MockAccommodationGatewayProvider())
    target.register(_MockWeatherGatewayProvider())


# ---------------------------------------------------------------------------
# Layer 2 — drop-in replacements for the plain Mock*Provider classes,
# matching each Discovery module's existing provider interface exactly.
# ---------------------------------------------------------------------------


class GatewayFlightProvider:
    """Same interface as ai.discovery.flights.flight_intelligence.MockFlightProvider
    — pass to FlightIntelligence(provider=GatewayFlightProvider()) and every
    call routes through the Intelligence Gateway instead."""

    def __init__(self, gateway: IntelligenceGateway | None = None) -> None:
        self._gateway = gateway or intelligence_gateway

    def search(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str | None,
        cabin_class: str,
    ) -> list[dict[str, Any]]:
        request = ProviderRequest(
            capability=Capability.FLIGHTS, operation="search",
            params={
                "origin": origin, "destination": destination, "departure_date": departure_date,
                "return_date": return_date, "cabin_class": cabin_class,
            },
        )
        result = self._gateway.execute(Capability.FLIGHTS, request)
        return result.data if result.ok and result.data is not None else []


class GatewayAccommodationProvider:
    """Same interface as MockAccommodationProvider — see GatewayFlightProvider."""

    def __init__(self, gateway: IntelligenceGateway | None = None) -> None:
        self._gateway = gateway or intelligence_gateway

    def search(self, destination: str, check_in_date: str, nights: int) -> list[dict[str, Any]]:
        request = ProviderRequest(
            capability=Capability.ACCOMMODATION, operation="search",
            params={"destination": destination, "check_in_date": check_in_date, "nights": nights},
        )
        result = self._gateway.execute(Capability.ACCOMMODATION, request)
        return result.data if result.ok and result.data is not None else []


class GatewayWeatherProvider:
    """Same interface as MockWeatherProvider (month/year/known_destinations)
    — see GatewayFlightProvider."""

    def __init__(self, gateway: IntelligenceGateway | None = None) -> None:
        self._gateway = gateway or intelligence_gateway

    def month(self, destination: str, month_of_travel: int) -> dict[str, Any]:
        request = ProviderRequest(
            capability=Capability.WEATHER, operation="month",
            params={"destination": destination, "month_of_travel": month_of_travel},
        )
        result = self._gateway.execute(Capability.WEATHER, request)
        if result.ok and result.data is not None:
            return result.data
        return {
            "destination": destination, "month_of_travel": month_of_travel,
            "matched": False, "season": "UNKNOWN", "avg_temp_c": None,
            "rainfall": "UNKNOWN", "humidity": "UNKNOWN", "daylight_hours": None,
            "hazards": [],
        }

    def year(self, destination: str) -> list[dict[str, Any]]:
        request = ProviderRequest(
            capability=Capability.WEATHER, operation="year", params={"destination": destination},
        )
        result = self._gateway.execute(Capability.WEATHER, request)
        return result.data if result.ok and result.data is not None else []

    def known_destinations(self) -> list[str]:
        request = ProviderRequest(capability=Capability.WEATHER, operation="known_destinations", params={})
        result = self._gateway.execute(Capability.WEATHER, request)
        return result.data if result.ok and result.data is not None else []


register_default_providers()
