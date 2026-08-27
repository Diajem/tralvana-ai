from __future__ import annotations

import pytest

from travelos.bookings.accommodation import AccommodationBookingCommand, AccommodationGuest
from travelos.intelligence_gateway.exceptions import (
    ProviderRateLimitedError,
    ProviderResponseError,
    ProviderValidationError,
)
from travelos.intelligence_gateway.provider_contract import ProviderRequest
from travelos.intelligence_gateway.provider_status import Capability
from travelos.live_providers.adapters.hbx_hotels_provider import (
    HbxHotelBookingClient,
    HbxHotelsProvider,
)
from travelos.live_providers.hbx_destination_catalog import (
    HbxDestination,
    InMemoryHbxDestinationCatalog,
)
from travelos.live_providers.transport import FakeTransport

_KEY = "hbx-test-key"
_SECRET = "hbx-test-secret"


@pytest.fixture(autouse=True)
def _credentials(monkeypatch):
    monkeypatch.setenv("HBX_HOTELS_API_KEY", _KEY)
    monkeypatch.setenv("HBX_HOTELS_SECRET", _SECRET)


def _request(**overrides) -> ProviderRequest:
    params = {
        "destination": "Manchester, UK",
        "country_code": "GB",
        "check_in_date": "2027-09-15",
        "nights": 3,
        "adults": 2,
        "children": 2,
        "child_ages": [7, 10],
        "rooms": 2,
    }
    params.update(overrides)
    return ProviderRequest(capability=Capability.ACCOMMODATION, operation="search", params=params)


def _catalog() -> InMemoryHbxDestinationCatalog:
    return InMemoryHbxDestinationCatalog(
        [HbxDestination(code="MAN", name="Manchester", country_code="GB")]
    )


def _availability_body() -> dict:
    return {
        "auditData": {"token": "request-token"},
        "hotels": {
            "hotels": [
                {
                    "code": 101,
                    "name": "HBX Test Hotel",
                    "currency": "GBP",
                    "categoryName": "4 STARS",
                    "destinationName": "Manchester",
                    "zoneName": "City Centre",
                    "latitude": "53.48",
                    "longitude": "-2.24",
                    "rooms": [
                        {
                            "code": "DBL.ST",
                            "name": "Double Standard",
                            "rates": [
                                {
                                    "rateKey": "rate-key-1",
                                    "rateType": "RECHECK",
                                    "rateClass": "NOR",
                                    "sellingRate": "450.00",
                                    "boardCode": "BB",
                                    "boardName": "BED AND BREAKFAST",
                                    "paymentType": "AT_WEB",
                                    "cancellationPolicies": [
                                        {"amount": "450.00", "from": "2027-09-14T00:00:00+00:00"}
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ]
        },
    }


def test_search_maps_destination_occupancy_rates_and_auth_headers():
    transport = FakeTransport.always_returning(200, _availability_body())
    provider = HbxHotelsProvider(transport=transport, destination_catalog=_catalog())

    result = provider.execute(_request())

    sent = transport.sent_requests[0]
    assert sent.url.endswith("/hotel-api/1.0/hotels")
    assert sent.headers["Api-key"] == _KEY
    assert len(sent.headers["X-Signature"]) == 64
    assert sent.json_body["destination"] == {"code": "MAN"}
    assert sent.json_body["stay"] == {"checkIn": "2027-09-15", "checkOut": "2027-09-18"}
    assert sent.json_body["occupancies"] == [
        {"rooms": 1, "adults": 1, "children": 1, "paxes": [{"type": "CH", "age": 7}]},
        {"rooms": 1, "adults": 1, "children": 1, "paxes": [{"type": "CH", "age": 10}]},
    ]
    assert result.data[0]["_provider_source"] == "hbx_hotels"
    assert result.data[0]["_provider_rate_id"] == "rate-key-1"
    assert result.data[0]["nightly_price"] == 150.0
    assert _SECRET not in repr(sent)


def test_search_requires_exact_child_ages_before_network_call():
    transport = FakeTransport.always_returning(200, _availability_body())
    provider = HbxHotelsProvider(transport=transport, destination_catalog=_catalog())

    with pytest.raises(ProviderValidationError):
        provider.execute(_request(child_ages=[7]))

    assert transport.sent_requests == []


def test_search_requires_cached_unambiguous_destination_before_network_call():
    transport = FakeTransport.always_returning(200, _availability_body())
    provider = HbxHotelsProvider(
        transport=transport, destination_catalog=InMemoryHbxDestinationCatalog()
    )

    with pytest.raises(ProviderValidationError):
        provider.execute(_request(destination="Unknown"))

    assert transport.sent_requests == []


def test_evaluation_quota_response_is_classified_without_leaking_secret():
    transport = FakeTransport.always_returning(
        403, {"error": {"code": "DAILY_QUOTA", "message": "Daily quota exceeded"}}
    )
    provider = HbxHotelsProvider(transport=transport, destination_catalog=_catalog())

    with pytest.raises(ProviderRateLimitedError) as exc_info:
        provider.execute(_request())

    assert "quota" in str(exc_info.value).lower()
    assert _SECRET not in str(exc_info.value)


def _command(**overrides) -> AccommodationBookingCommand:
    values = {
        "rate_reference": "bookable-rate-key",
        "holder_given_name": "Ada",
        "holder_family_name": "Lovelace",
        "guests": (
            AccommodationGuest(1, "ADULT", "Ada", "Lovelace"),
            AccommodationGuest(1, "CHILD", "Byron", "Lovelace", age=10),
        ),
        "client_reference": "TRALVANA-123",
        "customer_approved": True,
        "rate_status": "BOOKABLE",
        "expected_total": 450.0,
        "expected_currency": "GBP",
    }
    values.update(overrides)
    return AccommodationBookingCommand(**values)


def test_booking_requires_explicit_customer_approval_and_sends_nothing():
    transport = FakeTransport()
    client = HbxHotelBookingClient(transport)

    with pytest.raises(ProviderValidationError, match="approval"):
        client.create_booking(_command(customer_approved=False))

    assert transport.sent_requests == []


def test_booking_maps_guests_and_enforces_approved_price_boundary():
    response = {
        "booking": {
            "reference": "HBX-ABC",
            "clientReference": "TRALVANA-123",
            "status": "CONFIRMED",
            "totalSellingRate": "450.00",
            "currency": "GBP",
            "hotel": {"name": "HBX Test Hotel", "checkIn": "2027-09-15", "checkOut": "2027-09-18"},
        }
    }
    transport = FakeTransport.always_returning(200, response)
    booking = HbxHotelBookingClient(transport).create_booking(_command())

    sent = transport.sent_requests[0]
    assert sent.url.endswith("/bookings")
    assert sent.timeout_seconds >= 60
    assert sent.json_body["holder"] == {"name": "Ada", "surname": "Lovelace"}
    assert len(sent.json_body["rooms"]) == 1
    assert sent.json_body["rooms"][0]["paxes"][1]["age"] == 10
    assert booking.supplier_reference == "HBX-ABC"
    assert booking.total == 450.0


def test_booking_detail_is_available_without_a_mutation():
    response = {
        "booking": {
            "reference": "HBX-ABC",
            "clientReference": "TRALVANA-123",
            "status": "CONFIRMED",
            "totalNet": "430.00",
            "currency": "GBP",
            "hotel": {
                "name": "HBX Test Hotel",
                "checkIn": "2027-09-15",
                "checkOut": "2027-09-18",
                "rooms": [{"rates": [{"cancellationPolicies": [{"amount": "25.00"}]}]}],
            },
        }
    }
    transport = FakeTransport.always_returning(200, response)

    booking = HbxHotelBookingClient(transport).get_booking("HBX-ABC")

    assert transport.sent_requests[0].method == "GET"
    assert transport.sent_requests[0].url.endswith("/bookings/HBX-ABC")
    assert booking.hotel_name == "HBX Test Hotel"
    assert booking.cancellation_policies == ({"amount": "25.00"},)


def test_booking_rejects_supplier_confirmation_outside_customer_price_boundary():
    transport = FakeTransport.always_returning(
        200,
        {"booking": {"reference": "HBX-ABC", "totalSellingRate": "475.00", "currency": "GBP"}},
    )

    with pytest.raises(ProviderResponseError, match="price boundary"):
        HbxHotelBookingClient(transport).create_booking(_command())


def test_cancellation_simulation_is_safe_but_real_cancel_requires_approval():
    transport = FakeTransport.always_returning(
        200, {"booking": {"reference": "HBX-ABC", "status": "CANCELLED", "cancellationAmount": "25", "currency": "GBP"}}
    )
    client = HbxHotelBookingClient(transport)

    simulation = client.cancel_booking("HBX-ABC")
    assert simulation.simulated is True
    assert transport.sent_requests[0].query_params["cancellationFlag"] == "SIMULATION"

    with pytest.raises(ProviderValidationError, match="approval"):
        client.cancel_booking("HBX-ABC", simulate=False)
    assert len(transport.sent_requests) == 1
