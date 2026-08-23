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

T-025 initially wired Flight, Accommodation, and Weather only. T-053 adds
Events through the same two-layer pattern. Destinations/Budget/Visa/Maps/
Currency remain deferred.
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


class _MockEventGatewayProvider(Provider):
    def __init__(self) -> None:
        from ai.discovery.events.mock_event_provider import MockEventProvider
        self._provider = MockEventProvider()

    @property
    def provider_name(self) -> str:
        return "mock_event_provider"

    @property
    def capability(self) -> Capability:
        return Capability.EVENTS

    @property
    def priority(self) -> int:
        return 10

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "description": (
                "Deterministic curated event ideas — no live calendar, "
                "fixture, ticket, price, or availability data."
            )
        }

    def execute(self, request: ProviderRequest) -> ProviderResult:
        options = self._provider.search(**request.params)
        return ProviderResult(
            provider_name=self.provider_name,
            capability=self.capability,
            status=ProviderStatus.AVAILABLE,
            data=options,
            confidence=0.35,
            source_metadata={"mock": True, "date_specific": False},
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
    target.register(_MockEventGatewayProvider())


# ---------------------------------------------------------------------------
# Layer 2 — drop-in replacements for the plain Mock*Provider classes,
# matching each Discovery module's existing provider interface exactly.
# ---------------------------------------------------------------------------


class LiveFlightSearchUnavailableError(Exception):
    """Raised when TRALVANA_FLIGHT_PROVIDER_MODE=LIVE_SANDBOX and the
    Duffel search failed (auth, timeout, rate limit, malformed response,
    or simply no eligible provider) with mock fallback disabled — T-038's
    "LIVE_SANDBOX failure returns a clear safe error by default" rule.
    Caught at the API boundary (services/api/app/domains/flights/router.py)
    and converted to a 503, never silently swallowed into an empty result."""


class GatewayFlightProvider:
    """Same interface as ai.discovery.flights.flight_intelligence.MockFlightProvider
    — pass to FlightIntelligence(provider=GatewayFlightProvider()) and every
    call routes through the Intelligence Gateway instead.

    T-038 additions: `last_result` exposes the full ProviderResult from the
    most recent search() call (data_source/provider_status/request_id for
    the public API — see ai/discovery/flights/flight_intelligence.py),
    and a LIVE_SANDBOX failure either raises LiveFlightSearchUnavailableError
    or falls back to mock data, per TRALVANA_FLIGHT_MOCK_FALLBACK_ENABLED —
    but mock and live offers are never blended into one result set; a
    fallback response is 100% mock, clearly labelled as such."""

    def __init__(self, gateway: IntelligenceGateway | None = None) -> None:
        self._gateway = gateway or intelligence_gateway
        self.last_result: ProviderResult | None = None
        self.used_mock_fallback: bool = False

    def search(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str | None,
        cabin_class: str,
        adults: int = 1,
        minor_ages: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        self.used_mock_fallback = False
        request = ProviderRequest(
            capability=Capability.FLIGHTS, operation="search",
            params={
                "origin": origin, "destination": destination, "departure_date": departure_date,
                "return_date": return_date, "cabin_class": cabin_class,
                "adults": adults,
                "minor_ages": list(minor_ages or []),
            },
        )
        result = self._gateway.execute(Capability.FLIGHTS, request)
        self.last_result = result
        if result.ok and result.data is not None:
            return result.data

        from travelos.config.configuration_manager import config

        if config.flight_provider_mode != "LIVE_SANDBOX":
            # MOCK mode's own provider effectively never fails this way —
            # preserve the pre-T-038 behaviour of a quiet empty list.
            return []

        if config.flight_mock_fallback_enabled:
            from ai.discovery.flights.flight_intelligence import MockFlightProvider
            self.used_mock_fallback = True
            return MockFlightProvider().search(
                origin,
                destination,
                departure_date,
                return_date,
                cabin_class,
                adults,
                minor_ages or [],
            )

        raise LiveFlightSearchUnavailableError(
            "Duffel sandbox flight search is unavailable "
            f"(provider_status={result.status.value}); "
            "set TRALVANA_FLIGHT_MOCK_FALLBACK_ENABLED=true to fall back to mock data instead."
        )


class LiveAccommodationSearchUnavailableError(Exception):
    """Raised when TRALVANA_ACCOMMODATION_PROVIDER_MODE=LIVE_SANDBOX and
    the Duffel Stays search failed (auth, timeout, rate limit,
    malformed response, destination not resolvable, or simply no
    eligible provider) with mock fallback disabled — T-039's "LIVE_SANDBOX
    errors must be safe and clear" rule. Caught at the API boundary
    (services/api/app/domains/accommodation/router.py) and converted to
    a 503, never silently swallowed into an empty result."""


class GatewayAccommodationProvider:
    """Same interface as MockAccommodationProvider — see GatewayFlightProvider.

    T-039 additions: `last_result` exposes the full ProviderResult from
    the most recent search() call (data_source/provider_status/request_id
    for the public API — see ai/discovery/accommodation/accommodation_intelligence.py),
    adults/children/rooms are accepted and forwarded to the provider
    (MockAccommodationProvider ignores them, matching its pre-T-039
    behaviour exactly), and a LIVE_SANDBOX failure either raises
    LiveAccommodationSearchUnavailableError or falls back to mock data,
    per TRALVANA_ACCOMMODATION_MOCK_FALLBACK_ENABLED — mock and live
    properties are never blended into one result set; a fallback
    response is 100% mock, clearly labelled as such."""

    def __init__(self, gateway: IntelligenceGateway | None = None) -> None:
        self._gateway = gateway or intelligence_gateway
        self.last_result: ProviderResult | None = None
        self.used_mock_fallback: bool = False

    def search(
        self,
        destination: str,
        check_in_date: str,
        nights: int,
        adults: int = 1,
        children: int = 0,
        rooms: int = 1,
    ) -> list[dict[str, Any]]:
        self.used_mock_fallback = False
        request = ProviderRequest(
            capability=Capability.ACCOMMODATION, operation="search",
            params={
                "destination": destination, "check_in_date": check_in_date, "nights": nights,
                "adults": adults, "children": children, "rooms": rooms,
            },
        )
        result = self._gateway.execute(Capability.ACCOMMODATION, request)
        self.last_result = result
        if result.ok and result.data is not None:
            return result.data

        from travelos.config.configuration_manager import config

        if config.accommodation_provider_mode != "LIVE_SANDBOX":
            # MOCK mode's own provider effectively never fails this way —
            # preserve the pre-T-039 behaviour of a quiet empty list.
            return []

        if config.accommodation_mock_fallback_enabled:
            from ai.discovery.accommodation.mock_accommodation_provider import MockAccommodationProvider
            self.used_mock_fallback = True
            return MockAccommodationProvider().search(
                destination, check_in_date, nights, adults=adults, children=children, rooms=rooms
            )

        raise LiveAccommodationSearchUnavailableError(
            "Duffel Stays sandbox search is unavailable "
            f"(provider_status={result.status.value}); "
            "set TRALVANA_ACCOMMODATION_MOCK_FALLBACK_ENABLED=true to fall back to mock data instead."
        )


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


class GatewayEventProvider:
    """Provider-neutral event search interface.

    T-053 registers only a MOCK provider. A future live adapter can register
    for ``Capability.EVENTS`` without changing Event Intelligence, Trip Brain,
    the API, or the planner response contract.
    """

    def __init__(self, gateway: IntelligenceGateway | None = None) -> None:
        self._gateway = gateway or intelligence_gateway
        self.last_result: ProviderResult | None = None
        self.used_mock_fallback: bool = False

    def search(
        self,
        destination: str,
        start_date: str | None = None,
        end_date: str | None = None,
        interests: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        self.used_mock_fallback = False
        search_interests = _distinct_event_search_interests(interests or [])
        query_groups = (
            [[interest] for interest in search_interests]
            if len(search_interests) > 1
            else [list(search_interests)]
        )
        results = [
            self._gateway.execute(
                Capability.EVENTS,
                ProviderRequest(
                    capability=Capability.EVENTS,
                    operation="search",
                    params={
                        "destination": destination,
                        "start_date": start_date,
                        "end_date": end_date,
                        "interests": query_interests,
                    },
                ),
            )
            for query_interests in query_groups
        ]
        successful = [
            result
            for result in results
            if result.ok and result.data is not None
        ]
        if successful:
            records = _deduplicate_event_records(
                record
                for result in successful
                for record in result.data
            )
            self.last_result = _aggregate_event_results(
                results=results,
                successful=successful,
                data=records,
            )
            return records

        result = results[-1]
        self.last_result = result

        from travelos.config.configuration_manager import config

        if config.event_provider_mode != "LIVE":
            return []

        if config.event_mock_fallback_enabled:
            from ai.discovery.events.mock_event_provider import MockEventProvider

            self.used_mock_fallback = True
            return MockEventProvider().search(
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                interests=interests,
            )

        raise LiveEventSearchUnavailableError(
            "Ticketmaster live event search is unavailable "
            f"(provider_status={result.status.value}); "
            "set TRALVANA_EVENT_MOCK_FALLBACK_ENABLED=true to use clearly "
            "labelled curated fallback ideas."
        )


class LiveEventSearchUnavailableError(Exception):
    """A live event search failed and curated fallback is disabled."""


def _distinct_event_search_interests(interests: list[str]) -> list[str]:
    """Keep live fan-out bounded while preserving the traveller's ordering."""
    if any(
        " ".join(str(value).casefold().split()) in {"event", "events", "live event", "live events"}
        for value in interests
    ):
        # A generic event request should remain a broad destination/date
        # search. Sending "live events" as a Ticketmaster keyword can hide
        # valid concerts, theatre, sport and family listings.
        return []
    return list(
        dict.fromkeys(
            cleaned
            for value in interests
            if (cleaned := str(value).strip())
        )
    )[:4]


def _deduplicate_event_records(
    records,
) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    for record in records:
        provider_id = str(record.get("_provider_event_id", "")).strip()
        key = (
            ("provider", provider_id)
            if provider_id
            else (
                "canonical",
                str(record.get("name", "")).casefold(),
                str(record.get("starts_at", "")),
                str(record.get("venue_area", "")).casefold(),
            )
        )
        if key not in seen:
            seen.add(key)
            unique.append(record)
    return unique


def _aggregate_event_results(
    *,
    results: list[ProviderResult],
    successful: list[ProviderResult],
    data: list[dict[str, Any]],
) -> ProviderResult:
    primary = successful[0]
    all_succeeded = len(successful) == len(results)
    raw_count = sum(
        int(result.source_metadata.get("raw_event_count", 0) or 0)
        for result in successful
    )
    mapped_count = sum(
        int(result.source_metadata.get("mapped_event_count", 0) or 0)
        for result in successful
    )
    warnings = [
        warning
        for result in results
        for warning in result.warnings
    ]
    if not all_succeeded:
        warnings.append(
            f"{len(successful)} of {len(results)} interest-specific event "
            "searches succeeded"
        )
    return ProviderResult(
        provider_name=primary.provider_name,
        capability=Capability.EVENTS,
        status=(
            ProviderStatus.AVAILABLE if all_succeeded else ProviderStatus.DEGRADED
        ),
        data=data,
        confidence=min(result.confidence for result in successful),
        warnings=warnings,
        cached=all(result.cached for result in successful),
        stale=any(result.stale for result in successful),
        latency_ms=sum(result.latency_ms for result in results),
        request_id=primary.request_id,
        retrieved_at=max(result.retrieved_at for result in successful),
        source_metadata={
            **primary.source_metadata,
            "raw_event_count": raw_count,
            "mapped_event_count": mapped_count,
            "unique_event_count": len(data),
            "query_count": len(results),
            "successful_query_count": len(successful),
        },
    )


register_default_providers()
