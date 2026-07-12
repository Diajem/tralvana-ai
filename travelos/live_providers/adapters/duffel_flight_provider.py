"""
DuffelFlightProvider — the first real vendor adapter built on
BaseLiveProvider (T-026), for the FLIGHTS capability (T-027).

Duffel was selected over Amadeus, Kiwi/Tequila, and Skyscanner — see
docs/FIRST_LIVE_PROVIDER.md and docs/ADR/ADR-022-first-live-provider.md
for the full evaluation. In short: Duffel's authentication is a single
static bearer token (`BearerTokenAuthStrategy`, already fully
implemented), while every alternative with comparable self-serve sandbox
access requires an OAuth2 client-credentials exchange this framework
deliberately does not implement yet (TD-022).

Never registered automatically at import time (unlike the T-025 mock
providers in travelos/intelligence_gateway/discovery_adapters.py) —
`register_duffel_flight_provider()` must be called explicitly, because
this adapter has no real Transport to run against yet (only
`FakeTransport` exists, TD-021). Registering it unconditionally would
either silently do nothing useful (SANDBOX callers would get canned
FakeTransport data, not real Duffel offers) or invite someone to wire a
real Transport in before this repository is actually ready to make live
calls. See docs/FLIGHT_PROVIDER_INTEGRATION.md's "Enabling It" section.
"""

from __future__ import annotations

import re
from datetime import datetime
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

# Internal cabin_class <-> Duffel cabin_class. Duffel also supports
# "premium_economy", which has no internal equivalent (the Discovery
# Layer's three-tier _CABIN_ORDER in ai/discovery/flights/flight_intelligence.py
# is economy/business/first) — mapped down to "business" as the closest
# fit, documented once here rather than silently.
_CABIN_TO_DUFFEL = {"economy": "economy", "business": "business", "first": "first"}
_CABIN_FROM_DUFFEL = {"economy": "economy", "premium_economy": "business", "business": "business", "first": "first"}

# Duffel durations aren't always "PT#H#M" — a connection spanning past
# midnight (e.g. a long layover) is returned as "P1DT5H15M" (1 day, 5
# hours, 15 minutes), confirmed against a real SANDBOX response during
# T-037's live verification (docs/FIRST_LIVE_PROVIDER.md). The day
# component was absent from every documentation example this adapter
# was originally built against.
_ISO8601_DURATION_RE = re.compile(r"^P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?$")


class DuffelFlightProvider(BaseLiveProvider):
    """Production-shaped adapter for Duffel's Offer Requests API
    (https://duffel.com/docs/api/offer-requests). Implements only
    build_request()/parse_response() plus a Duffel-specific map_error() —
    every other lifecycle step (auth header injection, HTTP-status error
    mapping, metrics, tracing) is BaseLiveProvider's, unchanged.
    """

    def __init__(
        self,
        transport: Transport,
        token_env_var: str = "DUFFEL_API_TOKEN",
        environment: ProviderEnvironment = ProviderEnvironment.SANDBOX,
        priority: int = 10,
    ) -> None:
        super().__init__(
            provider_name="duffel_flight_provider",
            capability=Capability.FLIGHTS,
            environment=environment,
            transport=transport,
            auth=BearerTokenAuthStrategy(
                secret=SecretReference(
                    env_var=token_env_var,
                    required=True,
                    description="Duffel API token — a duffel_test_... token for SANDBOX, "
                    "never a duffel_live_... token outside PRODUCTION. See docs/FIRST_LIVE_PROVIDER.md.",
                )
            ),
            priority=priority,
        )
        self._last_response: TransportResponse | None = None

    # ------------------------------------------------------------------

    def supports(self, request: ProviderRequest) -> bool:
        return request.capability == self.capability and request.operation == "search"

    def build_request(self, request: ProviderRequest) -> TransportRequest:
        """Internal ProviderRequest (origin/destination/departure_date/
        return_date/cabin_class, exactly what GatewayFlightProvider.search()
        passes through) -> Duffel's offer_requests request shape. Never
        includes an auth header — authenticate() supplies that."""
        params = request.params
        slices: list[dict[str, str]] = [
            {
                "origin": params["origin"],
                "destination": params["destination"],
                "departure_date": params["departure_date"],
            }
        ]
        return_date = params.get("return_date")
        if return_date:
            slices.append(
                {
                    "origin": params["destination"],
                    "destination": params["origin"],
                    "departure_date": return_date,
                }
            )

        cabin_class = params.get("cabin_class", "economy")
        duffel_cabin_class = _CABIN_TO_DUFFEL.get(cabin_class, "economy")

        from travelos.config.configuration_manager import config

        return TransportRequest(
            method="POST",
            url=f"{_DUFFEL_BASE_URL}/air/offer_requests?return_offers=true",
            headers={
                "Duffel-Version": _DUFFEL_API_VERSION,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json_body={
                "data": {
                    "slices": slices,
                    "passengers": [{"type": "adult"}],
                    "cabin_class": duffel_cabin_class,
                }
            },
            timeout_seconds=config.provider_http_timeout_seconds,
        )

    def parse_response(self, response: TransportResponse) -> ProviderResult:
        """Duffel's offer_requests response -> ProviderResult whose `data`
        is a list of dicts in the exact shape
        ai/discovery/flights/flight_scorer.py, flight_reasoner.py, and
        flight_risk_assessor.py already expect from MockFlightProvider.search()
        — nothing Duffel-shaped leaks past this method."""
        body = response.body
        if not isinstance(body, dict) or "data" not in body:
            raise ProviderResponseError(f"{self.provider_name}: response missing 'data'")

        data = body["data"]
        if not isinstance(data, dict) or "offers" not in data:
            raise ProviderResponseError(f"{self.provider_name}: response missing 'data.offers'")

        offers = data["offers"]
        if not isinstance(offers, list):
            raise ProviderResponseError(f"{self.provider_name}: 'data.offers' is not a list")

        # Partial mapping failure (T-038): one malformed offer in a batch
        # of otherwise-good offers is skipped, not treated as a whole-
        # response failure — real Duffel responses can carry 200+ offers,
        # and discarding all of them over one bad entry would be a worse
        # outcome than surfacing the rest with a warning. Only if *every*
        # offer in a non-empty batch fails to map is this actually a
        # response-shape problem worth raising ProviderResponseError for.
        options: list[dict[str, Any]] = []
        failed_count = 0
        for offer in offers:
            try:
                options.append(self._map_offer(offer))
            except (KeyError, IndexError, TypeError, ValueError):
                failed_count += 1

        if offers and not options:
            raise ProviderResponseError(
                f"{self.provider_name}: all {len(offers)} offer(s) in the response failed to map"
            )

        return ProviderResult(
            provider_name=self.provider_name,
            capability=self.capability,
            status=ProviderStatus.AVAILABLE,
            data=options,
            confidence=0.9,
            warnings=(
                [f"{failed_count} of {len(offers)} offer(s) failed to map and were skipped"]
                if failed_count
                else []
            ),
            source_metadata={
                "provider_request_id": data.get("id", ""),
                "raw_offer_count": len(offers),
                "mapped_offer_count": len(options),
            },
        )

    def map_error(self, error: Exception) -> Exception:
        """Duffel returns a structured `{"errors": [{"type", "code", "message"}, ...]}`
        body even on failure statuses that BaseLiveProvider's generic
        HTTP-status mapping can't distinguish (e.g. 422 validation errors,
        which fall through to the generic ProviderResponseError). Inspect
        the stashed last response body (see send_request()) and refine
        when Duffel's own error type says more than the status code did."""
        last = self._last_response
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
        map_error() itself only ever receives the exception, not the
        response, so this is the one place that context can be captured."""
        response = super().send_request(transport_request)
        self._last_response = response
        return response

    # ------------------------------------------------------------------
    # Duffel offer -> internal flight-option dict
    # ------------------------------------------------------------------

    def _map_offer(self, offer: dict[str, Any]) -> dict[str, Any]:
        outbound = offer["slices"][0]
        segments = outbound["segments"]
        first_segment = segments[0]
        last_segment = segments[-1]

        stops = len(segments) - 1
        total_minutes = _parse_iso8601_duration(outbound["duration"])
        layover_minutes = _layover_minutes(segments) if stops >= 1 else 0

        duffel_cabin = first_segment["passengers"][0]["cabin_class"]
        cabin_class = _CABIN_FROM_DUFFEL.get(duffel_cabin, "economy")

        baggages = first_segment["passengers"][0].get("baggages", [])
        baggage_included = any(b.get("type") == "checked" and b.get("quantity", 0) > 0 for b in baggages)

        conditions = offer.get("conditions") or {}
        refund = (conditions.get("refund_before_departure") or {}).get("allowed", False)
        change = (conditions.get("change_before_departure") or {}).get("allowed", False)

        marketing_carrier = first_segment["marketing_carrier"]
        flight_number = f"{marketing_carrier['iata_code']}{first_segment['marketing_carrier_flight_number']}"

        return {
            "airline": offer["owner"]["name"],
            "flight_number": flight_number,
            "cabin_class": cabin_class,
            "stops": stops,
            "layover_duration": _fmt_duration(layover_minutes) if stops else "",
            "departure_time": _hhmm(first_segment["departing_at"]),
            "arrival_time": _hhmm(last_segment["arriving_at"]),
            "total_duration": _fmt_duration(total_minutes),
            "estimated_price": float(offer["total_amount"]),
            "currency": offer["total_currency"],
            "baggage_included": baggage_included,
            "refundability": "refundable" if refund else "non_refundable",
            "flexibility": "flexible" if change else "fixed",
            "departure_date": _date_part(first_segment["departing_at"]),
            "return_date": None,
            "_total_duration_minutes": total_minutes,
            "_layover_minutes": layover_minutes,
            # No independent price baseline is available from a single
            # offer_requests call — anchoring to its own price is a
            # neutral default (docs/FIRST_LIVE_PROVIDER.md's Known
            # Limitations), never an invented "typical" fare.
            "_price_anchor": float(offer["total_amount"]),
            # Preserved for future booking work only (T-038 explicitly
            # excludes booking) — popped before the public API response
            # in FlightIntelligence.recommend(), same as every other
            # underscore-prefixed internal field.
            "_provider_offer_id": offer["id"],
        }


def register_duffel_flight_provider(
    transport: Transport,
    registry: ProviderRegistry | None = None,
    token_env_var: str = "DUFFEL_API_TOKEN",
    environment: ProviderEnvironment = ProviderEnvironment.SANDBOX,
) -> DuffelFlightProvider:
    """Explicit, opt-in registration — never called automatically at
    import (see this module's docstring). `transport` must be supplied by
    the caller; there is no default because no real Transport exists yet
    (TD-021) and defaulting to FakeTransport here would look configured
    while silently returning canned data."""
    target = registry or provider_registry
    provider = DuffelFlightProvider(transport=transport, token_env_var=token_env_var, environment=environment)
    target.register(provider)
    return provider


# ---------------------------------------------------------------------------
# Small, dependency-free ISO 8601 / timestamp helpers — Duffel returns
# durations as "PT10H30M" and timestamps as "2026-10-01T14:00:00".
# ---------------------------------------------------------------------------


def _parse_iso8601_duration(duration: str) -> int:
    match = _ISO8601_DURATION_RE.match(duration)
    if not match:
        raise ValueError(f"unrecognised ISO 8601 duration: {duration!r}")
    days = int(match.group(1) or 0)
    hours = int(match.group(2) or 0)
    minutes = int(match.group(3) or 0)
    return days * 24 * 60 + hours * 60 + minutes


def _fmt_duration(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h}h {m}m" if h else f"{m}m"


def _hhmm(iso_timestamp: str) -> str:
    return datetime.fromisoformat(iso_timestamp).strftime("%H:%M")


def _date_part(iso_timestamp: str) -> str:
    return datetime.fromisoformat(iso_timestamp).strftime("%Y-%m-%d")


def _layover_minutes(segments: list[dict[str, Any]]) -> int:
    total = 0
    for prev, nxt in zip(segments, segments[1:]):
        arrival = datetime.fromisoformat(prev["arriving_at"])
        departure = datetime.fromisoformat(nxt["departing_at"])
        total += int((departure - arrival).total_seconds() // 60)
    return total
