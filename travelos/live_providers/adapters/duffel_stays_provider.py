"""
DuffelStaysProvider — the first live vendor adapter for the
ACCOMMODATION capability (T-039), built on BaseLiveProvider exactly
like DuffelFlightProvider (T-027) is for FLIGHTS. The two adapters
share almost no internal structure beyond that base class — per this
task's own "do not assume flight adapter structures apply to Stays"
instruction, confirmed true in two ways:

1. **Destination resolution.** Duffel Stays' location-based search
   requires geographic coordinates + a radius, not a place name —
   Tralvana's AccommodationIntelligence only ever has a destination
   *string* ("Tokyo", "Paris"). This adapter resolves that string to
   coordinates via Duffel's own Places API (`GET /places/suggestions`)
   as a private step inside `build_request()`, entirely self-contained
   — no Duffel-specific location data (place IDs, coordinates) ever
   reaches `ai/discovery/accommodation/` or any Tralvana domain model.

2. **Response shape.** Duffel Stays returns *raw, Duffel-vocabulary*
   records (`accommodation.rating`, `review_score`,
   `geographic_coordinates`, `amenities`, ...) — not already-scored
   internal fields the way a flight offer maps almost directly.
   `parse_response()` produces a raw record shaped like Duffel's own
   fields (tagged `_provider_source: "duffel_stays"`), mirroring
   `MockAccommodationProvider`'s own contract: "raw, provider-shaped
   records... the Normalizer's job is to absorb exactly this kind of
   inconsistency" (see that module's docstring).
   `AccommodationNormalizer.normalize()` gained a branch to handle it
   — see docs/DUFFEL_STAYS_INTEGRATION.md's Response Mapping section
   for the full field-by-field rationale, including which fields
   Duffel simply doesn't provide and how those are represented as
   neutral defaults, never fabricated values.

**Confirmed against the real Duffel API during this task**: the
existing `DUFFEL_API_TOKEN` (used for Flights sandbox testing since
T-027) does NOT have Stays access — a live call returns HTTP 403,
`"This feature is not enabled for your account."`. This adapter is
fully built and unit-tested against documented Duffel-shaped fixtures;
see docs/DUFFEL_STAYS_INTEGRATION.md's "Access Requirement" section for
exactly what's needed before a real sandbox call can succeed.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from travelos.intelligence_gateway.exceptions import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderValidationError,
)
from travelos.intelligence_gateway.provider_contract import ProviderRequest
from travelos.intelligence_gateway.provider_registry import ProviderRegistry, provider_registry
from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_status import Capability, ProviderEnvironment, ProviderStatus
from travelos.intelligence_gateway.secret_reference import SecretReference
from travelos.live_providers.auth.bearer_token_auth import BearerTokenAuthStrategy
from travelos.live_providers.base_live_provider import BaseLiveProvider
from travelos.live_providers.transport import Transport, TransportRequest, TransportResponse

_DUFFEL_BASE_URL = "https://api.duffel.com"
_DUFFEL_API_VERSION = "v2"

# Duffel's documented radius range is 1-100km (docs/DUFFEL_STAYS_INTEGRATION.md
# cites the source) — 15km is a reasonable engineering default for a
# city-wide search, not a value Duffel specifies; deliberately
# configurable via the constructor, not hardcoded as vendor guidance.
_DEFAULT_SEARCH_RADIUS_KM = 15.0


class DuffelStaysProvider(BaseLiveProvider):
    """Production-shaped adapter for Duffel Stays' Search API
    (`POST /stays/search`, https://duffel.com/docs/api/v2/search).
    Implements build_request()/parse_response() plus a Duffel-specific
    map_error() and a private destination-resolution step — every other
    lifecycle step (auth header injection, HTTP-status error mapping,
    metrics, tracing) is BaseLiveProvider's, unchanged."""

    def __init__(
        self,
        transport: Transport,
        token_env_var: str = "DUFFEL_API_TOKEN",
        environment: ProviderEnvironment = ProviderEnvironment.SANDBOX,
        priority: int = 10,
        search_radius_km: float = _DEFAULT_SEARCH_RADIUS_KM,
    ) -> None:
        super().__init__(
            provider_name="duffel_stays_provider",
            capability=Capability.ACCOMMODATION,
            environment=environment,
            transport=transport,
            auth=BearerTokenAuthStrategy(
                secret=SecretReference(
                    env_var=token_env_var,
                    required=True,
                    description="Duffel API token — the same credential DuffelFlightProvider "
                    "uses. Stays access must be separately enabled on the Duffel account "
                    "(docs/DUFFEL_STAYS_INTEGRATION.md's Access Requirement section) — a "
                    "present, valid token for Flights does not guarantee Stays access.",
                )
            ),
            priority=priority,
        )
        self._search_radius_km = search_radius_km
        self._last_response: TransportResponse | None = None
        # parse_response() only ever receives the TransportResponse, not
        # the original ProviderRequest — these are stashed by
        # build_request() so parse_response() can still attach
        # destination/check_in_date/nights/search-coordinates to every
        # mapped result.
        self._last_search_coordinates: tuple[float, float] | None = None
        self._last_search_params: dict[str, Any] = {}

    # ------------------------------------------------------------------

    def supports(self, request: ProviderRequest) -> bool:
        return request.capability == self.capability and request.operation == "search"

    def build_request(self, request: ProviderRequest) -> TransportRequest:
        """Internal ProviderRequest (destination/check_in_date/nights/
        adults/children/rooms, from GatewayAccommodationProvider.search()
        — the same params MockAccommodationProvider.search() takes, plus
        adults/children/rooms it accepts and ignores) -> Duffel's
        stays/search request shape. Resolves `destination` to coordinates
        via a private Places API call first — see _resolve_destination().
        Duffel needs check_out_date, not nights — computed here, the one
        exact, non-fabricated conversion between the two representations."""
        params = request.params
        latitude, longitude = self._resolve_destination(params["destination"])

        nights = params.get("nights", 1)
        check_in_date = params["check_in_date"]
        check_out_date = (
            datetime.strptime(check_in_date, "%Y-%m-%d") + timedelta(days=nights)
        ).strftime("%Y-%m-%d")

        self._last_search_params = {
            "destination": params["destination"],
            "check_in_date": check_in_date,
            "nights": nights,
        }

        from travelos.config.configuration_manager import config

        return TransportRequest(
            method="POST",
            url=f"{_DUFFEL_BASE_URL}/stays/search",
            headers={
                "Duffel-Version": _DUFFEL_API_VERSION,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json_body={
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                "rooms": params.get("rooms", 1),
                "guests": _build_guests(params.get("adults", 1), params.get("children", 0)),
                "location": {
                    "geographic_coordinates": {"latitude": latitude, "longitude": longitude},
                    "radius": self._search_radius_km,
                },
            },
            timeout_seconds=config.provider_http_timeout_seconds,
        )

    def parse_response(self, response: TransportResponse) -> ProviderResult:
        """Duffel's stays/search response -> ProviderResult whose `data`
        is a list of *raw, Duffel-vocabulary* dicts (never the internal
        canonical accommodation shape) — AccommodationNormalizer.normalize()
        is where those get converted, exactly as it already does for
        MockAccommodationProvider's own raw records."""
        body = response.body
        if not isinstance(body, dict) or "data" not in body:
            raise ProviderResponseError(f"{self.provider_name}: response missing 'data'")

        data = body["data"]
        if not isinstance(data, dict) or "results" not in data:
            raise ProviderResponseError(f"{self.provider_name}: response missing 'data.results'")

        results = data["results"]
        if not isinstance(results, list):
            raise ProviderResponseError(f"{self.provider_name}: 'data.results' is not a list")

        search_lat = self._last_search_coordinates[0] if self._last_search_coordinates else None
        search_lng = self._last_search_coordinates[1] if self._last_search_coordinates else None
        check_in_date = self._last_search_params.get("check_in_date", "")
        nights = self._last_search_params.get("nights", 1)
        destination = self._last_search_params.get("destination", "")

        options: list[dict[str, Any]] = []
        failed_count = 0
        for result in results:
            try:
                options.append(
                    self._map_search_result(result, destination, search_lat, search_lng, check_in_date, nights)
                )
            except (KeyError, IndexError, TypeError, ValueError):
                failed_count += 1

        if results and not options:
            raise ProviderResponseError(
                f"{self.provider_name}: all {len(results)} search result(s) failed to map"
            )

        return ProviderResult(
            provider_name=self.provider_name,
            capability=self.capability,
            status=ProviderStatus.AVAILABLE,
            data=options,
            confidence=0.85,
            warnings=(
                [f"{failed_count} of {len(results)} search result(s) failed to map and were skipped"]
                if failed_count
                else []
            ),
            source_metadata={
                "raw_result_count": len(results),
                "mapped_result_count": len(options),
            },
        )

    def map_error(self, error: Exception) -> Exception:
        """Duffel's structured `{"errors": [...]}` body — same pattern as
        DuffelFlightProvider.map_error() — plus the account-not-enabled
        403 this task's own access check surfaced (a plain-text 403
        body, not JSON, confirmed against the real API)."""
        last = self._last_response
        if last is not None and last.status_code == 403 and isinstance(last.body, str):
            if "not enabled for your account" in last.body.lower():
                return ProviderValidationError(
                    f"{self.provider_name}: Duffel Stays is not enabled for this account "
                    "(docs/DUFFEL_STAYS_INTEGRATION.md's Access Requirement section)"
                )

        body = last.body if last is not None else None
        if isinstance(body, dict):
            duffel_errors = body.get("errors")
            if isinstance(duffel_errors, list) and duffel_errors:
                first = duffel_errors[0] if isinstance(duffel_errors[0], dict) else {}
                error_type = first.get("type", "")
                code = first.get("code", "")
                label = f"{error_type}/{code}" if code else (error_type or "duffel_error")
                message = f"{self.provider_name}: {label} — {first.get('message', '')}"
                if error_type == "validation_error":
                    return ProviderValidationError(message)
                if error_type == "authentication_error":
                    return ProviderAuthenticationError(message)
                if error_type == "rate_limit_error":
                    return ProviderRateLimitError(message)
        return super().map_error(error)

    def send_request(self, transport_request: TransportRequest) -> TransportResponse:
        """Stashes the raw response so map_error() can inspect Duffel's
        structured error body after _check_response_status() raises —
        same pattern as DuffelFlightProvider.send_request()."""
        response = super().send_request(transport_request)
        self._last_response = response
        return response

    # ------------------------------------------------------------------
    # Destination resolution — Duffel-specific, never leaks past this class
    # ------------------------------------------------------------------

    def _resolve_destination(self, destination: str) -> tuple[float, float]:
        """destination string -> (latitude, longitude) via Duffel's
        Places API (GET /places/suggestions). A second, self-contained
        transport call — this class's own authenticate() supplies the
        header, since build_request()'s own auth header is only merged
        in by execute() afterward, too late for this inner call."""
        transport_request = TransportRequest(
            method="GET",
            url=f"{_DUFFEL_BASE_URL}/places/suggestions",
            headers={**self.authenticate(), "Duffel-Version": _DUFFEL_API_VERSION, "Accept": "application/json"},
            query_params={"query": destination},
            timeout_seconds=10.0,
        )
        response = self.send_request(transport_request)
        self._check_places_response_status(response)

        body = response.body
        if not isinstance(body, dict) or not isinstance(body.get("data"), list):
            raise ProviderResponseError(f"{self.provider_name}: places lookup returned an unexpected shape")

        # Confirmed against the real Duffel API during T-039's live
        # verification: a "city" place is often returned with
        # latitude/longitude both null (Duffel has no single canonical
        # point for it), while "airport" places for the same query
        # reliably carry coordinates. Preferring the first *geocoded*
        # place — city first, then any other type — is the only
        # approach that actually resolves real destinations; taking the
        # first city match unconditionally (this adapter's original
        # assumption, before this was discovered) fails whenever that
        # city itself lacks coordinates.
        places = [p for p in body["data"] if isinstance(p, dict)]
        geocoded = [p for p in places if p.get("latitude") is not None and p.get("longitude") is not None]
        place = next((p for p in geocoded if p.get("type") == "city"), None) or (geocoded[0] if geocoded else None)
        if not place:
            raise ProviderValidationError(
                f"{self.provider_name}: could not resolve destination {destination!r} to a location "
                "(no geocoded place found)"
            )

        latitude, longitude = float(place["latitude"]), float(place["longitude"])
        self._last_search_coordinates = (latitude, longitude)
        return latitude, longitude

    def _check_places_response_status(self, response: TransportResponse) -> None:
        if 200 <= response.status_code < 300:
            return
        if response.status_code in (401, 403):
            raise ProviderAuthenticationError(f"{self.provider_name}: places lookup returned HTTP {response.status_code}")
        if response.status_code == 429:
            raise ProviderRateLimitError(f"{self.provider_name}: places lookup returned HTTP 429")
        raise ProviderResponseError(f"{self.provider_name}: places lookup returned HTTP {response.status_code}")

    # ------------------------------------------------------------------
    # Duffel search result -> raw (Duffel-vocabulary) accommodation dict
    # ------------------------------------------------------------------

    def _map_search_result(
        self,
        result: dict[str, Any],
        destination: str,
        search_lat: float | None,
        search_lng: float | None,
        check_in_date: str,
        nights: int,
    ) -> dict[str, Any]:
        accommodation = result["accommodation"]
        location = accommodation.get("location") or {}
        geo = location.get("geographic_coordinates") or {}
        address = location.get("address") or {}

        rooms = accommodation.get("rooms") or []
        cheapest_rate = _cheapest_rate(rooms)

        if cheapest_rate is not None:
            total_amount = cheapest_rate["total_amount"]
            currency = cheapest_rate["total_currency"]
            board_type = cheapest_rate.get("board_type")
            cancellation_timeline = cheapest_rate.get("cancellation_timeline")
            rate_id = cheapest_rate.get("id")
        else:
            # Per Duffel's own docs: "a search result's accommodation may
            # not include rooms and rates information... but you will
            # always know the price of the cheapest rate" — the
            # search-result-level cheapest_rate_* fields are the fallback.
            total_amount = result["cheapest_rate_total_amount"]
            currency = result["cheapest_rate_currency"]
            board_type = None
            cancellation_timeline = None
            rate_id = result.get("id")

        total_price = float(total_amount)
        nightly_price = round(total_price / nights, 2) if nights else total_price

        return {
            "_provider_source": "duffel_stays",
            "_destination": destination,
            "_provider_property_id": accommodation["id"],
            "_provider_rate_id": rate_id,
            "property_name": accommodation["name"],
            "duffel_rating": accommodation.get("rating"),
            "duffel_review_score": accommodation.get("review_score"),
            "duffel_review_count": accommodation.get("review_count"),
            "duffel_amenities": accommodation.get("amenities") or [],
            "duffel_latitude": geo.get("latitude"),
            "duffel_longitude": geo.get("longitude"),
            "duffel_city_name": address.get("city_name"),
            "duffel_region": address.get("region"),
            "search_latitude": search_lat,
            "search_longitude": search_lng,
            "nightly_price": nightly_price,
            "total_price": total_price,
            "currency": currency,
            "board_type": board_type,
            "cancellation_timeline": cancellation_timeline,
            "check_in_date": check_in_date,
            "nights": nights,
        }


def register_duffel_stays_provider(
    transport: Transport,
    registry: ProviderRegistry | None = None,
    token_env_var: str = "DUFFEL_API_TOKEN",
    environment: ProviderEnvironment = ProviderEnvironment.SANDBOX,
) -> DuffelStaysProvider:
    """Explicit, opt-in registration — never called automatically at
    import, matching register_duffel_flight_provider()'s (T-027)
    pattern. `transport` must be supplied by the caller."""
    target = registry or provider_registry
    provider = DuffelStaysProvider(transport=transport, token_env_var=token_env_var, environment=environment)
    target.register(provider)
    return provider


def _build_guests(adults: int, children: int) -> list[dict[str, Any]]:
    guests: list[dict[str, Any]] = [{"type": "adult"} for _ in range(max(adults, 1))]
    guests.extend({"type": "child"} for _ in range(max(children, 0)))
    return guests


def _cheapest_rate(rooms: list[dict[str, Any]]) -> dict[str, Any] | None:
    cheapest: dict[str, Any] | None = None
    cheapest_amount: float | None = None
    for room in rooms:
        for rate in room.get("rates") or []:
            try:
                amount = float(rate["total_amount"])
            except (KeyError, TypeError, ValueError):
                continue
            if cheapest_amount is None or amount < cheapest_amount:
                cheapest, cheapest_amount = rate, amount
    return cheapest
