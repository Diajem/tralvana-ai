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
            {"products": [{"productCode": "LON-123", "title": "London tour"}]},
        )
    if request.url.endswith("/products/LON-123"):
        return TransportResponse(200, {"productCode": "LON-123", "title": "Tour"})
    if request.url.endswith("/availability/schedules/LON-123"):
        return TransportResponse(200, {"productCode": "LON-123", "bookableItems": []})
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
