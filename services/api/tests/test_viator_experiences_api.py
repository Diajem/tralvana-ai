from __future__ import annotations

from app.domains.experiences.service import ExperienceDiscoveryService
from travelos.live_providers.adapters.viator_experience_provider import (
    ViatorExperienceProvider,
)
from travelos.live_providers.transport import (
    FakeTransport,
    TransportRequest,
    TransportResponse,
)


def _responder(request: TransportRequest) -> TransportResponse:
    if request.url.endswith("/destinations"):
        return TransportResponse(
            200,
            {
                "destinations": [
                    {
                        "destinationId": 684,
                        "name": "London",
                        "type": "CITY",
                        "parentDestinationId": 51,
                        "countryCode": "GB",
                    },
                    {
                        "destinationId": 51,
                        "name": "England",
                        "type": "COUNTRY",
                    },
                ]
            },
        )
    if request.url.endswith("/products/search"):
        return TransportResponse(
            200,
            {"products": [
                {"productCode": "LON-123", "title": "London tour"},
                {
                    "productCode": "LON-TRANSFER",
                    "title": "Private airport transfer to your London hotel",
                },
            ]},
        )
    if request.url.endswith("/products/LON-123"):
        return TransportResponse(200, {"productCode": "LON-123", "title": "Tour"})
    if request.url.endswith("/availability/schedules/LON-123"):
        return TransportResponse(200, {"productCode": "LON-123", "bookableItems": []})
    raise AssertionError(f"Unexpected request: {request.url}")


def _global_responder(request: TransportRequest) -> TransportResponse:
    if request.url.endswith("/destinations"):
        return TransportResponse(
            200,
            {
                "destinations": [
                    {"destinationId": 1, "name": "United States", "type": "COUNTRY", "countryCode": "US"},
                    {"destinationId": 2, "name": "England", "type": "COUNTRY", "countryCode": "GB"},
                    {"destinationId": 3, "name": "Australia", "type": "COUNTRY", "countryCode": "AU"},
                    {"destinationId": 4, "name": "Canada", "type": "COUNTRY", "countryCode": "CA"},
                    {"destinationId": 5, "name": "United Arab Emirates", "type": "COUNTRY", "countryCode": "AE"},
                    {"destinationId": 6, "name": "Japan", "type": "COUNTRY", "countryCode": "JP"},
                    {"destinationId": 7, "name": "South Africa", "type": "COUNTRY", "countryCode": "ZA"},
                    {"destinationId": 8, "name": "Jamaica", "type": "COUNTRY", "countryCode": "JM"},
                    {"destinationId": 101, "name": "York", "type": "CITY", "parentDestinationId": 2},
                    {"destinationId": 102, "name": "New York City", "type": "CITY", "parentDestinationId": 1},
                    {"destinationId": 103, "name": "Sydney", "type": "CITY", "parentDestinationId": 3},
                    {"destinationId": 104, "name": "Sydney", "type": "CITY", "parentDestinationId": 4},
                    {"destinationId": 105, "name": "Dubai", "type": "CITY", "parentDestinationId": 5},
                    {"destinationId": 106, "name": "Tokyo", "type": "CITY", "parentDestinationId": 6},
                    {"destinationId": 107, "name": "Cape Town", "type": "CITY", "parentDestinationId": 7},
                    {"destinationId": 108, "name": "Montego Bay", "type": "CITY", "parentDestinationId": 8},
                ]
            },
        )
    if request.url.endswith("/products/search"):
        destination_id = request.json_body["filtering"]["destination"]
        return TransportResponse(
            200,
            {"products": [{"productCode": f"DEST-{destination_id}", "title": "Matched tour"}]},
        )
    raise AssertionError(f"Unexpected request: {request.url}")


def _service(monkeypatch) -> tuple[ExperienceDiscoveryService, FakeTransport]:
    monkeypatch.setenv("TEST_VIATOR_KEY", "fixture-key")
    transport = FakeTransport(_responder)
    provider = ViatorExperienceProvider(
        transport,
        api_key_env_var="TEST_VIATOR_KEY",
    )
    return ExperienceDiscoveryService(provider), transport


def test_search_resolves_destination_name_and_returns_non_bookable_products(
    monkeypatch,
):
    service, transport = _service(monkeypatch)

    result = service.search(
        destination="London, England",
        start_date="2026-10-10",
        end_date="2026-10-12",
        currency="GBP",
        count=20,
    )

    assert result["destination"] == "London"
    assert result["destination_id"] == "684"
    assert result["products"][0]["product_reference"] == "LON-123"
    assert result["products"][0]["service_type"] == "EXPERIENCE"
    assert result["products"][1]["service_type"] == "TRANSFER"
    assert result["booking_enabled"] is False
    assert transport.sent_requests[1].json_body["filtering"]["destination"] == "684"

    service.search(
        destination="London",
        start_date=None,
        end_date=None,
        currency="GBP",
        count=5,
    )
    destination_requests = [
        request
        for request in transport.sent_requests
        if request.url.endswith("/destinations")
    ]
    assert len(destination_requests) == 1


def test_details_can_include_the_availability_schedule(monkeypatch):
    service, _ = _service(monkeypatch)

    result = service.details("LON-123", currency="GBP", include_schedule=True)

    assert result["product"]["productCode"] == "LON-123"
    assert result["availability_schedule"]["bookableItems"] == []
    assert result["environment"] == "SANDBOX"
    assert result["booking_enabled"] is False


def test_global_city_resolution_uses_country_and_parent_hierarchy(monkeypatch):
    monkeypatch.setenv("TEST_VIATOR_KEY", "fixture-key")
    transport = FakeTransport(_global_responder)
    service = ExperienceDiscoveryService(
        ViatorExperienceProvider(transport, api_key_env_var="TEST_VIATOR_KEY")
    )

    cases = {
        "New York City, USA": ("102", "US"),
        "Sydney, Australia": ("103", "AU"),
        "Sydney, Canada": ("104", "CA"),
        "Dubai, United Arab Emirates": ("105", "AE"),
        "Tokyo, Japan": ("106", "JP"),
        "Cape Town, South Africa": ("107", "ZA"),
        "Montego Bay, Jamaica": ("108", "JM"),
    }
    for requested, (destination_id, country_code) in cases.items():
        result = service.search(
            destination=requested,
            start_date="2026-10-10",
            end_date="2026-10-12",
            currency="GBP",
            count=6,
        )
        assert result["destination_id"] == destination_id
        assert result["country_code"] == country_code
        assert result["products"][0]["product_reference"] == f"DEST-{destination_id}"


def test_ambiguous_city_without_country_fails_closed(monkeypatch):
    monkeypatch.setenv("TEST_VIATOR_KEY", "fixture-key")
    service = ExperienceDiscoveryService(
        ViatorExperienceProvider(
            FakeTransport(_global_responder), api_key_env_var="TEST_VIATOR_KEY"
        )
    )

    import pytest

    with pytest.raises(ValueError, match="ambiguous"):
        service.search(
            destination="Sydney",
            start_date=None,
            end_date=None,
            currency="GBP",
            count=6,
        )


def test_partial_name_does_not_match_another_city(monkeypatch):
    monkeypatch.setenv("TEST_VIATOR_KEY", "fixture-key")
    service = ExperienceDiscoveryService(
        ViatorExperienceProvider(
            FakeTransport(_global_responder), api_key_env_var="TEST_VIATOR_KEY"
        )
    )

    import pytest

    with pytest.raises(ValueError, match="not found"):
        service.search(
            destination="New York City, United Kingdom",
            start_date=None,
            end_date=None,
            currency="GBP",
            count=6,
        )
