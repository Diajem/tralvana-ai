from __future__ import annotations

import pytest

from travelos.intelligence_gateway.exceptions import ProviderRateLimitedError
from travelos.live_providers.hbx_content_sync import HbxDestinationContentSync
from travelos.live_providers.hbx_destination_catalog import InMemoryHbxDestinationCatalog
from travelos.live_providers.transport import FakeTransport, TransportResponse


@pytest.fixture(autouse=True)
def _credentials(monkeypatch):
    monkeypatch.setenv("HBX_HOTELS_API_KEY", "test-key")
    monkeypatch.setenv("HBX_HOTELS_SECRET", "test-secret")


def test_content_sync_pages_and_upserts_without_exposing_secrets():
    page_one = {
        "destinations": {
            "total": 3,
            "destinations": [
                {"code": "MAN", "name": "Manchester", "countryCode": "GB", "zones": []},
                {"code": "LON", "name": "London", "countryCode": "GB", "zones": [{"zoneCode": 1}]},
            ],
        }
    }
    page_two = {
        "destinations": {
            "total": 3,
            "destinations": [
                {"code": "ROM", "name": "Rome", "countryCode": "IT", "zones": []}
            ],
        }
    }
    responses = iter([page_one, page_two])
    transport = FakeTransport(
        responder=lambda request: TransportResponse(status_code=200, body=next(responses))
    )
    catalog = InMemoryHbxDestinationCatalog()

    result = HbxDestinationContentSync(transport, catalog).sync(page_size=2, max_pages=3)

    assert result.pages_requested == 2
    assert result.destinations_upserted == 3
    assert result.complete is True
    assert catalog.resolve("Manchester", "GB").code == "MAN"
    assert transport.sent_requests[0].query_params["from"] == "1"
    assert transport.sent_requests[1].query_params["from"] == "3"
    assert "test-secret" not in repr(transport.sent_requests)


def test_content_sync_stops_at_page_limit_and_returns_resume_index():
    body = {
        "destinations": [
            {"code": "MAN", "name": "Manchester", "countryCode": "GB"},
            {"code": "LON", "name": "London", "countryCode": "GB"},
        ],
        "total": 10,
    }
    transport = FakeTransport.always_returning(200, body)

    result = HbxDestinationContentSync(
        transport, InMemoryHbxDestinationCatalog()
    ).sync(page_size=2, max_pages=1)

    assert result.complete is False
    assert result.next_index == 3
    assert len(transport.sent_requests) == 1


def test_content_sync_advances_past_invalid_supplier_rows():
    body = {
        "destinations": [
            {"code": "BAD", "name": "Missing country"},
            {"code": "MAN", "name": "Manchester", "countryCode": "GB"},
        ],
        "total": 10,
    }
    transport = FakeTransport.always_returning(200, body)

    result = HbxDestinationContentSync(
        transport, InMemoryHbxDestinationCatalog()
    ).sync(page_size=2, max_pages=1)

    assert result.destinations_received == 1
    assert result.next_index == 3


def test_content_sync_classifies_quota_failure():
    transport = FakeTransport.always_returning(429, {"error": {"message": "quota"}})

    with pytest.raises(ProviderRateLimitedError):
        HbxDestinationContentSync(transport, InMemoryHbxDestinationCatalog()).sync()
