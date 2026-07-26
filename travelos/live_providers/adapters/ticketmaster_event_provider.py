"""Ticketmaster Discovery API adapter for live event search (T-054).

The adapter translates Ticketmaster's vendor response into the canonical
event record consumed by Event Intelligence. It discovers public listings
only: it does not reserve, purchase, or claim ticket availability.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any
from urllib.parse import urlparse

from travelos.intelligence_gateway.exceptions import (
    ProviderResponseError,
    ProviderValidationError,
)
from travelos.intelligence_gateway.provider_contract import ProviderRequest
from travelos.intelligence_gateway.provider_registry import (
    ProviderRegistry,
    provider_registry,
)
from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_status import (
    Capability,
    ProviderEnvironment,
    ProviderStatus,
)
from travelos.intelligence_gateway.secret_reference import SecretReference
from travelos.live_providers.auth.api_key_auth import ApiKeyAuthStrategy
from travelos.live_providers.base_live_provider import BaseLiveProvider
from travelos.live_providers.transport import (
    Transport,
    TransportRequest,
    TransportResponse,
)

_BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"
_WORD_RE = re.compile(r"[a-z0-9]+")
_STATUS_MAP = {
    "onsale": "ON_SALE",
    "offsale": "OFF_SALE",
    "cancelled": "CANCELLED",
    "canceled": "CANCELLED",
    "postponed": "POSTPONED",
    "rescheduled": "RESCHEDULED",
}
_CATEGORY_MAP = {
    "sports": "SPORT",
    "arts & theatre": "CULTURE",
    "music": "MUSIC",
    "film": "FILM",
    "family": "FAMILY",
}


class TicketmasterEventProvider(BaseLiveProvider):
    """Live, read-only Ticketmaster Discovery event adapter."""

    def __init__(
        self,
        transport: Transport,
        api_key_env_var: str = "TICKETMASTER_API_KEY",
        priority: int = 10,
    ) -> None:
        api_key = SecretReference(
            env_var=api_key_env_var,
            required=True,
            description="Ticketmaster Discovery API consumer key",
        )
        super().__init__(
            provider_name="ticketmaster_event_provider",
            capability=Capability.EVENTS,
            environment=ProviderEnvironment.PRODUCTION,
            transport=transport,
            auth=ApiKeyAuthStrategy(secret=api_key),
            priority=priority,
        )
        self._api_key = api_key
        self._last_response: TransportResponse | None = None

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "description": "Live public event listings from Ticketmaster Discovery API.",
            "discovery_only": True,
            "booking_enabled": False,
        }

    def supports(self, request: ProviderRequest) -> bool:
        return request.capability == self.capability and request.operation == "search"

    def authenticate(self) -> dict[str, str]:
        """Ticketmaster authenticates with ``apikey`` in the query string."""
        if not self._api_key.is_present():
            # Reuse the standard strategy's safe missing-key error.
            self._auth.headers()
        return {}

    def build_request(self, request: ProviderRequest) -> TransportRequest:
        params = request.params
        destination = str(params.get("destination", "")).strip()
        if not destination:
            raise ProviderValidationError(
                f"{self.provider_name}: destination is required"
            )

        start_date = _validated_date(params.get("start_date"), "start_date")
        end_date = _validated_date(params.get("end_date"), "end_date")
        if start_date and end_date and end_date < start_date:
            raise ProviderValidationError(
                f"{self.provider_name}: end_date must be on or after start_date"
            )

        query = {
            "apikey": self._api_key.resolve(),
            "city": destination,
            "locale": "*",
            "size": "20",
            "sort": "date,asc",
            "includeTBA": "no",
            "includeTBD": "no",
            "includeTest": "no",
        }
        if start_date:
            query["startDateTime"] = f"{start_date.isoformat()}T00:00:00Z"
        if end_date:
            query["endDateTime"] = f"{end_date.isoformat()}T23:59:59Z"

        interests = [
            str(value).strip()
            for value in params.get("interests", [])
            if str(value).strip()
        ]
        # A single keyword is a useful vendor filter. With several distinct
        # interests, keep the destination/date search broad and let Tralvana's
        # provider-neutral scorer rank the returned classifications instead of
        # inventing undocumented Ticketmaster boolean-query syntax.
        if len(interests) == 1:
            query["keyword"] = interests[0]

        from travelos.config.configuration_manager import config

        return TransportRequest(
            method="GET",
            url=_BASE_URL,
            headers={"Accept": "application/json"},
            query_params=query,
            timeout_seconds=config.provider_http_timeout_seconds,
        )

    def parse_response(self, response: TransportResponse) -> ProviderResult:
        body = response.body
        if not isinstance(body, dict):
            raise ProviderResponseError(
                f"{self.provider_name}: response body is not an object"
            )

        embedded = body.get("_embedded")
        if embedded is None:
            events: list[Any] = []
        elif not isinstance(embedded, dict):
            raise ProviderResponseError(
                f"{self.provider_name}: '_embedded' is not an object"
            )
        else:
            events = embedded.get("events", [])
            if not isinstance(events, list):
                raise ProviderResponseError(
                    f"{self.provider_name}: '_embedded.events' is not a list"
                )

        options: list[dict[str, Any]] = []
        failed_count = 0
        for event in events:
            try:
                options.append(_map_event(event))
            except (KeyError, TypeError, ValueError):
                failed_count += 1

        if events and not options:
            raise ProviderResponseError(
                f"{self.provider_name}: all {len(events)} event(s) failed to map"
            )

        page = body.get("page") if isinstance(body.get("page"), dict) else {}
        return ProviderResult(
            provider_name=self.provider_name,
            capability=self.capability,
            status=ProviderStatus.AVAILABLE,
            data=options,
            confidence=0.9,
            warnings=(
                [f"{failed_count} of {len(events)} event(s) failed to map and were skipped"]
                if failed_count
                else []
            ),
            source_metadata={
                "raw_event_count": len(events),
                "mapped_event_count": len(options),
                "total_elements": page.get("totalElements"),
                "discovery_only": True,
            },
        )

    def send_request(self, transport_request: TransportRequest) -> TransportResponse:
        response = super().send_request(transport_request)
        self._last_response = response
        return response

    def map_error(self, error: Exception) -> Exception:
        if (
            self._last_response is not None
            and self._last_response.status_code == 400
        ):
            return ProviderValidationError(
                f"{self.provider_name}: Ticketmaster rejected the search parameters"
            )
        return super().map_error(error)


def register_ticketmaster_event_provider(
    transport: Transport,
    registry: ProviderRegistry | None = None,
    api_key_env_var: str = "TICKETMASTER_API_KEY",
) -> TicketmasterEventProvider:
    target = registry or provider_registry
    provider = TicketmasterEventProvider(
        transport=transport,
        api_key_env_var=api_key_env_var,
    )
    target.register(provider)
    return provider


def _validated_date(value: Any, field_name: str) -> date | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ProviderValidationError(
            f"ticketmaster_event_provider: {field_name} must be YYYY-MM-DD"
        ) from exc


def _map_event(event: Any) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise TypeError("event is not an object")

    name = str(event["name"]).strip()
    if not name:
        raise ValueError("event name is empty")

    venues = (
        event.get("_embedded", {}).get("venues", [])
        if isinstance(event.get("_embedded"), dict)
        else []
    )
    venue = venues[0] if venues and isinstance(venues[0], dict) else {}
    destination = _nested_name(venue, "city") or _nested_name(venue, "country")
    venue_area = _venue_area(venue)

    dates = event.get("dates") if isinstance(event.get("dates"), dict) else {}
    start = dates.get("start") if isinstance(dates.get("start"), dict) else {}
    end = dates.get("end") if isinstance(dates.get("end"), dict) else {}
    starts_at = _event_datetime(start)
    ends_at = _event_datetime(end)

    classifications = [
        value
        for value in event.get("classifications", [])
        if isinstance(value, dict)
    ]
    category, tags = _classification_data(classifications, name)
    status = dates.get("status") if isinstance(dates.get("status"), dict) else {}
    availability = _STATUS_MAP.get(
        str(status.get("code", "")).lower(),
        "UNKNOWN",
    )
    ticket_url = _safe_public_url(event.get("url"))
    description = _description(event)

    return {
        "destination": destination,
        "name": name,
        "category": category,
        "venue_area": venue_area,
        "description": description,
        "tags": tags,
        "starts_at": starts_at,
        "ends_at": ends_at,
        "availability_status": availability,
        "ticket_url": ticket_url,
        "requires_ticket": ticket_url is not None,
        "source_name": "Ticketmaster Discovery API",
        "evidence_level": "LIVE",
        "_provider_event_id": str(event.get("id", "")),
    }


def _event_datetime(value: dict[str, Any]) -> str | None:
    if value.get("dateTime"):
        return str(value["dateTime"])
    local_date = value.get("localDate")
    local_time = value.get("localTime")
    if local_date and local_time:
        return f"{local_date}T{local_time}"
    return str(local_date) if local_date else None


def _classification_data(
    classifications: list[dict[str, Any]],
    name: str,
) -> tuple[str, list[str]]:
    tags = set(_WORD_RE.findall(name.lower()))
    category = "OTHER"
    for classification in classifications:
        for field in ("segment", "genre", "subGenre", "type", "subType"):
            value = classification.get(field)
            if not isinstance(value, dict) or not value.get("name"):
                continue
            label = str(value["name"]).strip().lower()
            tags.add(label)
            tags.update(_WORD_RE.findall(label))
            if field == "segment" and category == "OTHER":
                category = _CATEGORY_MAP.get(label, label.upper())

    if "sports" in tags:
        tags.update({"sport", "match"})
    if "soccer" in tags:
        tags.update({"football", "sport", "match"})
    if "football" in tags:
        tags.update({"soccer", "sport", "match"})
    return category, sorted(tags)


def _nested_name(value: dict[str, Any], key: str) -> str:
    nested = value.get(key)
    return str(nested.get("name", "")).strip() if isinstance(nested, dict) else ""


def _venue_area(venue: dict[str, Any]) -> str:
    parts = [
        str(venue.get("name", "")).strip(),
        _nested_name(venue, "city"),
        _nested_name(venue, "state"),
        _nested_name(venue, "country"),
    ]
    return ", ".join(dict.fromkeys(part for part in parts if part))


def _description(event: dict[str, Any]) -> str:
    for key in ("info", "pleaseNote"):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "Live public event listing retrieved from Ticketmaster Discovery API."


def _safe_public_url(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    return value if parsed.scheme == "https" and bool(parsed.hostname) else None
