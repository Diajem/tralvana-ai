"""HBX Hotels search and transactional sandbox adapters.

The search provider plugs into Tralvana's existing Intelligence Gateway for
provider priority/failover.  Transactional operations use a separate,
provider-neutral booking contract because booking and cancellation must never
be cached or retried as ordinary discovery searches.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from travelos.bookings.accommodation import (
    AccommodationBooking,
    AccommodationBookingCommand,
    AccommodationCancellation,
    AccommodationRateQuote,
)
from travelos.config.configuration_manager import config
from travelos.intelligence_gateway.exceptions import (
    ProviderAuthenticationError,
    ProviderError,
    ProviderRateLimitedError,
    ProviderResponseError,
    ProviderUnavailableError,
    ProviderValidationError,
)
from travelos.intelligence_gateway.provider_contract import ProviderRequest
from travelos.intelligence_gateway.provider_registry import ProviderRegistry, provider_registry
from travelos.intelligence_gateway.provider_result import ProviderResult
from travelos.intelligence_gateway.provider_status import Capability, ProviderEnvironment, ProviderStatus
from travelos.intelligence_gateway.secret_reference import SecretReference
from travelos.live_providers.auth.hbx_signature_auth import HbxSignatureAuthStrategy
from travelos.live_providers.base_live_provider import BaseLiveProvider
from travelos.live_providers.hbx_destination_catalog import HbxDestinationCatalog
from travelos.live_providers.transport import Transport, TransportRequest, TransportResponse

_HBX_TEST_BASE_URL = "https://api.test.hotelbeds.com/hotel-api/1.0"
_HBX_PRODUCTION_BASE_URL = "https://api.hotelbeds.com/hotel-api/1.0"
_DEFAULT_MAX_HOTELS = 50
_DEFAULT_MAX_RATES_PER_ROOM = 3
_BOOKING_CONFIRMATION_TIMEOUT_SECONDS = 60.0


def _auth(
    api_key_env_var: str = "HBX_HOTELS_API_KEY",
    secret_env_var: str = "HBX_HOTELS_SECRET",
) -> HbxSignatureAuthStrategy:
    return HbxSignatureAuthStrategy(
        api_key=SecretReference(api_key_env_var, description="HBX Hotels API key"),
        shared_secret=SecretReference(secret_env_var, description="HBX Hotels shared secret"),
    )


def _base_url(environment: ProviderEnvironment) -> str:
    return _HBX_PRODUCTION_BASE_URL if environment == ProviderEnvironment.PRODUCTION else _HBX_TEST_BASE_URL


class HbxHotelsProvider(BaseLiveProvider):
    """Live HBX availability adapter for ``Capability.ACCOMMODATION``."""

    def __init__(
        self,
        transport: Transport,
        destination_catalog: HbxDestinationCatalog,
        api_key_env_var: str = "HBX_HOTELS_API_KEY",
        secret_env_var: str = "HBX_HOTELS_SECRET",
        environment: ProviderEnvironment = ProviderEnvironment.SANDBOX,
        priority: int = 10,
        max_hotels: int = _DEFAULT_MAX_HOTELS,
        max_rates_per_room: int = _DEFAULT_MAX_RATES_PER_ROOM,
    ) -> None:
        super().__init__(
            provider_name="hbx_hotels_provider",
            capability=Capability.ACCOMMODATION,
            environment=environment,
            transport=transport,
            auth=_auth(api_key_env_var, secret_env_var),
            priority=priority,
        )
        self._catalog = destination_catalog
        self._base_url = _base_url(environment)
        self._max_hotels = max_hotels
        self._max_rates_per_room = max_rates_per_room
        self._last_search: dict[str, Any] = {}
        self._last_response: TransportResponse | None = None

    def supports(self, request: ProviderRequest) -> bool:
        return request.capability == self.capability and request.operation == "search"

    def build_request(self, request: ProviderRequest) -> TransportRequest:
        params = request.params
        destination_name = str(params.get("destination") or "").strip()
        country_code = str(params.get("country_code") or "").strip() or None
        destination = self._catalog.resolve(destination_name, country_code)
        if destination is None:
            raise ProviderValidationError(
                f"{self.provider_name}: no unique cached HBX destination code for {destination_name!r}; "
                "run the HBX destination catalogue sync before live searching"
            )

        check_in = _required_date(params.get("check_in_date"), "check_in_date")
        nights = _positive_int(params.get("nights", 1), "nights")
        check_out = (datetime.strptime(check_in, "%Y-%m-%d") + timedelta(days=nights)).strftime("%Y-%m-%d")
        adults = _positive_int(params.get("adults", 1), "adults")
        rooms = _positive_int(params.get("rooms", 1), "rooms")
        child_ages = _child_ages(params)
        occupancies = _build_occupancies(adults=adults, child_ages=child_ages, rooms=rooms)

        self._last_search = {
            "destination": destination_name,
            "destination_code": destination.code,
            "check_in_date": check_in,
            "check_out_date": check_out,
            "nights": nights,
        }
        return TransportRequest(
            method="POST",
            url=f"{self._base_url}/hotels",
            headers=_json_headers(),
            json_body={
                "stay": {"checkIn": check_in, "checkOut": check_out},
                "occupancies": occupancies,
                "destination": {"code": destination.code},
                "filter": {
                    "maxHotels": self._max_hotels,
                    "maxRatesPerRoom": self._max_rates_per_room,
                },
            },
            timeout_seconds=config.provider_http_timeout_seconds,
        )

    def send_request(self, transport_request: TransportRequest) -> TransportResponse:
        response = super().send_request(transport_request)
        self._last_response = response
        return response

    def parse_response(self, response: TransportResponse) -> ProviderResult:
        body = response.body
        hotels_container = body.get("hotels") if isinstance(body, dict) else None
        hotels = hotels_container.get("hotels") if isinstance(hotels_container, dict) else None
        if not isinstance(hotels, list):
            raise ProviderResponseError(f"{self.provider_name}: response missing hotels.hotels")

        mapped: list[dict[str, Any]] = []
        failed = 0
        for hotel in hotels:
            for room in hotel.get("rooms", []) if isinstance(hotel, dict) else []:
                for rate in room.get("rates", []) if isinstance(room, dict) else []:
                    try:
                        mapped.append(self._map_rate(hotel, room, rate))
                    except (KeyError, TypeError, ValueError, ZeroDivisionError):
                        failed += 1
        raw_rate_count = len(mapped) + failed
        if raw_rate_count and not mapped:
            raise ProviderResponseError(
                f"{self.provider_name}: all {raw_rate_count} availability rate(s) failed to map"
            )

        audit = body.get("auditData") if isinstance(body, dict) else {}
        warnings = [f"{failed} of {raw_rate_count} HBX rate(s) failed to map and were skipped"] if failed else []
        return ProviderResult(
            provider_name=self.provider_name,
            capability=self.capability,
            status=ProviderStatus.AVAILABLE,
            data=mapped,
            confidence=0.95,
            warnings=warnings,
            source_metadata={
                "provider_environment": self.environment.value,
                "provider_request_id": (audit or {}).get("token") or (audit or {}).get("serverId"),
                "destination_code": self._last_search.get("destination_code"),
                "raw_result_count": raw_rate_count,
                "mapped_result_count": len(mapped),
            },
        )

    def map_error(self, error: Exception) -> Exception:
        if isinstance(error, ProviderError):
            response = self._last_response
            detail = _hbx_error_detail(response.body if response else None)
            if response and response.status_code == 403 and any(
                marker in detail.casefold() for marker in ("quota", "rate limit", "too many")
            ):
                return ProviderRateLimitedError(f"{self.provider_name}: HBX evaluation quota exceeded")
            if response and response.status_code in (400, 422):
                return ProviderValidationError(f"{self.provider_name}: {detail or 'HBX rejected the request'}")
            if response and response.status_code in (401, 403):
                return ProviderAuthenticationError(f"{self.provider_name}: HBX rejected the credentials")
            return error
        return super().map_error(error)

    def _map_rate(self, hotel: dict[str, Any], room: dict[str, Any], rate: dict[str, Any]) -> dict[str, Any]:
        nights = int(self._last_search["nights"])
        total = _price_for_display(rate)
        currency = str(hotel["currency"])
        return {
            "_provider_source": "hbx_hotels",
            "_provider_property_id": str(hotel["code"]),
            "_provider_rate_id": str(rate["rateKey"]),
            "_destination": self._last_search["destination"],
            "property_name": str(hotel["name"]),
            "hbx_category_name": str(hotel.get("categoryName") or ""),
            "hbx_destination_name": str(hotel.get("destinationName") or ""),
            "hbx_zone_name": str(hotel.get("zoneName") or ""),
            "hbx_latitude": _optional_float(hotel.get("latitude")),
            "hbx_longitude": _optional_float(hotel.get("longitude")),
            "room_code": str(room.get("code") or ""),
            "room_name": str(room.get("name") or ""),
            "rate_type": str(rate.get("rateType") or ""),
            "rate_class": str(rate.get("rateClass") or ""),
            "rate_comments_id": rate.get("rateCommentsId"),
            "board_code": str(rate.get("boardCode") or ""),
            "board_name": str(rate.get("boardName") or ""),
            "payment_type": str(rate.get("paymentType") or ""),
            "packaging": bool(rate.get("packaging", False)),
            "total_price": total,
            "nightly_price": round(total / nights, 2),
            "currency": currency,
            "cancellation_policies": list(rate.get("cancellationPolicies") or []),
            "taxes": list((rate.get("taxes") or {}).get("taxes") or []),
            "check_in_date": self._last_search["check_in_date"],
            "check_out_date": self._last_search["check_out_date"],
            "nights": nights,
        }


class HbxHotelBookingClient:
    """HBX check-rate, booking and cancellation implementation.

    This client is intentionally not registered with the discovery gateway:
    transactional calls must never be cached or automatically replayed.
    """

    provider_name = "hbx_hotels_provider"

    def __init__(
        self,
        transport: Transport,
        api_key_env_var: str = "HBX_HOTELS_API_KEY",
        secret_env_var: str = "HBX_HOTELS_SECRET",
        environment: ProviderEnvironment = ProviderEnvironment.SANDBOX,
    ) -> None:
        self._transport = transport
        self._auth = _auth(api_key_env_var, secret_env_var)
        self._base_url = _base_url(environment)
        self.environment = environment

    def check_rate(self, rate_reference: str) -> AccommodationRateQuote:
        if not rate_reference:
            raise ProviderValidationError("HBX rate_reference is required")
        body = self._request("POST", "/checkrates", {"rooms": [{"rateKey": rate_reference}]})
        hotel, _room, rate = _first_booking_rate(body)
        total = _price_for_display(rate, hotel)
        return AccommodationRateQuote(
            provider_name=self.provider_name,
            rate_reference=str(rate["rateKey"]),
            status=str(rate.get("rateType") or ""),
            total=total,
            currency=str(hotel.get("currency") or body.get("currency") or ""),
            rate_comments=str(rate.get("rateComments") or ""),
            cancellation_policies=tuple(rate.get("cancellationPolicies") or []),
            taxes=tuple((rate.get("taxes") or {}).get("taxes") or []),
            raw_reference=str(rate.get("rateKey") or ""),
        )

    def create_booking(self, command: AccommodationBookingCommand) -> AccommodationBooking:
        if not command.customer_approved:
            raise ProviderValidationError("Explicit customer approval is required before booking")
        if command.rate_status.upper() != "BOOKABLE":
            raise ProviderValidationError("The selected HBX rate must be BOOKABLE before confirmation")
        if command.expected_total is None or not command.expected_currency:
            raise ProviderValidationError("A verified expected total and currency are required before booking")
        if command.expected_total < 0:
            raise ProviderValidationError("expected_total must not be negative")
        if not 0 <= command.price_tolerance_percent <= 100:
            raise ProviderValidationError("price_tolerance_percent must be between 0 and 100")
        if not command.rate_reference:
            raise ProviderValidationError("rate_reference is required")
        if not command.holder_given_name.strip() or not command.holder_family_name.strip():
            raise ProviderValidationError("holder given name and family name are required")
        if not command.guests:
            raise ProviderValidationError("At least one accommodation guest is required")
        if not command.client_reference or len(command.client_reference) > 20:
            raise ProviderValidationError("client_reference is required and must be at most 20 characters")

        paxes: list[dict[str, Any]] = []
        for guest in command.guests:
            if guest.guest_type not in ("ADULT", "CHILD"):
                raise ProviderValidationError("guest_type must be ADULT or CHILD")
            pax = {
                "roomId": guest.room_id,
                "type": "AD" if guest.guest_type == "ADULT" else "CH",
                "name": guest.given_name,
                "surname": guest.family_name,
            }
            if guest.guest_type == "CHILD":
                if guest.age is None or isinstance(guest.age, bool) or not 0 <= guest.age <= 17:
                    raise ProviderValidationError("Every child guest requires an age between 0 and 17")
                pax["age"] = guest.age
            if guest.room_id < 1:
                raise ProviderValidationError("Every guest requires a positive room_id")
            paxes.append(pax)

        payload: dict[str, Any] = {
            "holder": {
                "name": command.holder_given_name,
                "surname": command.holder_family_name,
            },
            # One HBX rateKey represents the selected availability rate. All
            # paxes stay under that rate entry and roomId assigns each person
            # to the correct room; repeating the same rateKey per room is not
            # HBX's documented confirmation shape.
            "rooms": [{"rateKey": command.rate_reference, "paxes": paxes}],
            "clientReference": command.client_reference,
            "tolerance": command.price_tolerance_percent,
        }
        if command.remark:
            payload["remark"] = command.remark
        body = self._request("POST", "/bookings", payload)
        booking = body.get("booking") if isinstance(body, dict) else None
        if not isinstance(booking, dict):
            raise ProviderResponseError("HBX booking response missing booking")

        total = _optional_float(booking.get("totalSellingRate") or booking.get("totalNet"))
        if total is None:
            raise ProviderResponseError("HBX booking response missing total")
        currency = str(booking.get("currency") or "")
        allowed_delta = command.expected_total * max(command.price_tolerance_percent, 0.0) / 100
        if currency != command.expected_currency or abs(total - command.expected_total) > allowed_delta + 0.01:
            raise ProviderResponseError("HBX confirmed a booking outside the customer-approved price boundary")

        return _map_booking(booking, default_client_reference=command.client_reference)

    def get_booking(self, supplier_reference: str) -> AccommodationBooking:
        if not supplier_reference:
            raise ProviderValidationError("supplier_reference is required")
        body = self._request("GET", f"/bookings/{supplier_reference}")
        booking = body.get("booking") if isinstance(body, dict) else None
        if not isinstance(booking, dict):
            raise ProviderResponseError("HBX booking detail response missing booking")
        return _map_booking(booking)

    def cancel_booking(
        self, supplier_reference: str, *, simulate: bool = True, customer_approved: bool = False
    ) -> AccommodationCancellation:
        if not supplier_reference:
            raise ProviderValidationError("supplier_reference is required")
        if not simulate and not customer_approved:
            raise ProviderValidationError("Explicit customer approval is required before cancellation")
        flag = "SIMULATION" if simulate else "CANCELLATION"
        body = self._request(
            "DELETE",
            f"/bookings/{supplier_reference}",
            query_params={"cancellationFlag": flag},
        )
        booking = body.get("booking") if isinstance(body, dict) else None
        booking = booking if isinstance(booking, dict) else {}
        cancellation_value = booking.get("cancellationAmount") or booking.get("totalNet")
        if cancellation_value is None and isinstance(body, dict):
            cancellation_value = body.get("cancellationAmount")
        amount = _optional_float(cancellation_value)
        return AccommodationCancellation(
            provider_name=self.provider_name,
            supplier_reference=str(booking.get("reference") or supplier_reference),
            status=str(booking.get("status") or ("SIMULATED" if simulate else "CANCELLED")),
            simulated=simulate,
            cancellation_amount=amount,
            currency=str(booking.get("currency") or body.get("currency") or "") or None,
        )

    def _request(
        self,
        method: str,
        path: str,
        json_body: dict[str, Any] | None = None,
        query_params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        headers = {**_json_headers(), **self._auth.headers()}
        response = self._transport.send(
            TransportRequest(
                method=method,
                url=f"{self._base_url}{path}",
                headers=headers,
                query_params=query_params or {},
                json_body=json_body,
                timeout_seconds=(
                    max(config.provider_http_timeout_seconds, _BOOKING_CONFIRMATION_TIMEOUT_SECONDS)
                    if method == "POST" and path == "/bookings"
                    else config.provider_http_timeout_seconds
                ),
            )
        )
        if not 200 <= response.status_code < 300:
            detail = _hbx_error_detail(response.body)
            if response.status_code in (401, 403):
                raise ProviderAuthenticationError("HBX rejected the booking credentials")
            if response.status_code in (400, 404, 409, 422):
                raise ProviderValidationError(f"HBX rejected the booking operation: {detail}")
            if response.status_code == 429:
                raise ProviderRateLimitedError("HBX booking API rate limit reached")
            raise ProviderUnavailableError(f"HBX booking API returned HTTP {response.status_code}")
        if not isinstance(response.body, dict):
            raise ProviderResponseError("HBX booking API returned a non-object response")
        return response.body


def register_hbx_hotels_provider(
    transport: Transport,
    destination_catalog: HbxDestinationCatalog,
    registry: ProviderRegistry | None = None,
    environment: ProviderEnvironment = ProviderEnvironment.SANDBOX,
    priority: int = 10,
) -> HbxHotelsProvider:
    provider = HbxHotelsProvider(
        transport=transport,
        destination_catalog=destination_catalog,
        environment=environment,
        priority=priority,
    )
    (registry or provider_registry).register(provider)
    return provider


def _json_headers() -> dict[str, str]:
    return {"Accept": "application/json", "Accept-Encoding": "gzip", "Content-Type": "application/json"}


def _required_date(value: Any, name: str) -> str:
    try:
        parsed = datetime.strptime(str(value), "%Y-%m-%d")
    except (TypeError, ValueError) as exc:
        raise ProviderValidationError(f"{name} must be in YYYY-MM-DD format") from exc
    return parsed.strftime("%Y-%m-%d")


def _positive_int(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ProviderValidationError(f"{name} must be a positive integer")
    return value


def _child_ages(params: dict[str, Any]) -> list[int]:
    children = int(params.get("children", 0) or 0)
    raw = params.get("child_ages") or []
    if not isinstance(raw, list) or any(not isinstance(age, int) or isinstance(age, bool) for age in raw):
        raise ProviderValidationError("child ages must be whole numbers between 0 and 17")
    ages = list(raw)
    if children != len(ages):
        raise ProviderValidationError(
            "HBX requires one explicit age for every child in an accommodation search"
        )
    if any(age < 0 or age > 17 for age in ages):
        raise ProviderValidationError("child ages must be between 0 and 17")
    return ages


def _build_occupancies(adults: int, child_ages: list[int], rooms: int) -> list[dict[str, Any]]:
    if adults < rooms:
        raise ProviderValidationError("HBX requires at least one adult in every requested room")
    adult_counts = [1] * rooms
    for index in range(adults - rooms):
        adult_counts[index % rooms] += 1
    children_by_room: list[list[int]] = [[] for _ in range(rooms)]
    for index, age in enumerate(child_ages):
        children_by_room[index % rooms].append(age)
    occupancies: list[dict[str, Any]] = []
    for room_index in range(rooms):
        ages = children_by_room[room_index]
        occupancy: dict[str, Any] = {
            "rooms": 1,
            "adults": adult_counts[room_index],
            "children": len(ages),
        }
        if ages:
            occupancy["paxes"] = [{"type": "CH", "age": age} for age in ages]
        occupancies.append(occupancy)
    return occupancies


def _price_for_display(rate: dict[str, Any], hotel: dict[str, Any] | None = None) -> float:
    value = rate.get("sellingRate") or rate.get("net")
    if value is None and hotel:
        value = hotel.get("totalSellingRate") or hotel.get("totalNet")
    parsed = _optional_float(value)
    if parsed is None:
        raise ProviderResponseError("HBX rate is missing a usable total price")
    return parsed


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _hbx_error_detail(body: Any) -> str:
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            return str(error.get("message") or error.get("description") or error.get("code") or "")
        errors = body.get("errors")
        if isinstance(errors, list) and errors:
            first = errors[0]
            if isinstance(first, dict):
                return str(first.get("message") or first.get("description") or first.get("code") or "")
        return str(body.get("message") or body.get("description") or "")
    return str(body or "")


def _first_booking_rate(body: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    hotels = body.get("hotel") or body.get("hotels")
    if isinstance(hotels, dict):
        hotels = hotels.get("hotels") or [hotels]
    if not isinstance(hotels, list) or not hotels:
        raise ProviderResponseError("HBX check-rate response missing hotel")
    hotel = hotels[0]
    rooms = hotel.get("rooms") if isinstance(hotel, dict) else None
    if not isinstance(rooms, list) or not rooms:
        raise ProviderResponseError("HBX check-rate response missing room")
    room = rooms[0]
    rates = room.get("rates") if isinstance(room, dict) else None
    if not isinstance(rates, list) or not rates:
        raise ProviderResponseError("HBX check-rate response missing rate")
    return hotel, room, rates[0]


def _map_booking(
    booking: dict[str, Any], default_client_reference: str = ""
) -> AccommodationBooking:
    total = _optional_float(booking.get("totalSellingRate") or booking.get("totalNet"))
    if total is None:
        raise ProviderResponseError("HBX booking response missing total")
    currency = str(booking.get("currency") or "")
    if not currency:
        raise ProviderResponseError("HBX booking response missing currency")
    hotel = booking.get("hotel") if isinstance(booking.get("hotel"), dict) else {}
    return AccommodationBooking(
        provider_name="hbx_hotels_provider",
        supplier_reference=str(booking.get("reference") or ""),
        client_reference=str(booking.get("clientReference") or default_client_reference),
        status=str(booking.get("status") or "CONFIRMED"),
        total=total,
        currency=currency,
        hotel_name=str(hotel.get("name") or ""),
        check_in_date=str(hotel.get("checkIn") or ""),
        check_out_date=str(hotel.get("checkOut") or ""),
        cancellation_policies=_booking_cancellation_policies(booking, hotel),
    )


def _booking_cancellation_policies(
    booking: dict[str, Any], hotel: dict[str, Any]
) -> tuple[dict[str, Any], ...]:
    direct = booking.get("cancellationPolicies")
    if isinstance(direct, list):
        return tuple(item for item in direct if isinstance(item, dict))
    policies: list[dict[str, Any]] = []
    for room in hotel.get("rooms", []) if isinstance(hotel.get("rooms"), list) else []:
        for rate in room.get("rates", []) if isinstance(room, dict) else []:
            if not isinstance(rate, dict):
                continue
            policies.extend(
                item for item in (rate.get("cancellationPolicies") or [])
                if isinstance(item, dict)
            )
    return tuple(policies)


def _star_rating(category_name: str) -> int:
    match = re.search(r"([1-5])", category_name or "")
    return int(match.group(1)) if match else 0
