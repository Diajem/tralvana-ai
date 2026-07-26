from __future__ import annotations

import pytest

from travelos.intelligence_gateway.exceptions import (
    ProviderAuthenticationError,
    ProviderResponseError,
    ProviderValidationError,
)
from travelos.intelligence_gateway.provider_contract import ProviderRequest
from travelos.intelligence_gateway.provider_status import (
    Capability,
    ProviderEnvironment,
    ProviderStatus,
)
from travelos.live_providers.adapters.ticketmaster_event_provider import (
    TicketmasterEventProvider,
)
from travelos.live_providers.transport import FakeTransport

_KEY_ENV = "TICKETMASTER_API_KEY"


def _request(**params) -> ProviderRequest:
    return ProviderRequest(
        capability=Capability.EVENTS,
        operation="search",
        params={
            "destination": "New York",
            "start_date": "2026-08-07",
            "end_date": "2026-08-22",
            "interests": ["soccer"],
            **params,
        },
    )


def _event(
    *,
    event_id: str = "evt-1",
    name: str = "New York City FC",
    status: str = "onsale",
    url: str = "https://www.ticketmaster.com/event/evt-1",
) -> dict:
    return {
        "id": event_id,
        "name": name,
        "url": url,
        "info": "A live public event listing.",
        "dates": {
            "start": {
                "localDate": "2026-08-15",
                "localTime": "19:30:00",
                "dateTime": "2026-08-15T23:30:00Z",
            },
            "status": {"code": status},
        },
        "classifications": [
            {
                "segment": {"name": "Sports"},
                "genre": {"name": "Soccer"},
            }
        ],
        "_embedded": {
            "venues": [
                {
                    "name": "Yankee Stadium",
                    "city": {"name": "New York"},
                    "state": {"name": "New York"},
                    "country": {"name": "United States"},
                }
            ]
        },
    }


def _body(*events: dict) -> dict:
    return {
        "_embedded": {"events": list(events)},
        "page": {"totalElements": len(events)},
    }


@pytest.fixture(autouse=True)
def _clean_key(monkeypatch):
    monkeypatch.delenv(_KEY_ENV, raising=False)


def test_provider_is_production_events_only():
    provider = TicketmasterEventProvider(transport=FakeTransport())
    assert provider.environment == ProviderEnvironment.PRODUCTION
    assert provider.capability == Capability.EVENTS
    assert provider.supports(_request())
    assert not provider.supports(
        ProviderRequest(capability=Capability.EVENTS, operation="details")
    )


def test_request_maps_destination_dates_and_single_interest(monkeypatch):
    monkeypatch.setenv(_KEY_ENV, "consumer-key-for-test")
    transport = FakeTransport.always_returning(200, _body())
    provider = TicketmasterEventProvider(transport=transport)
    provider.execute(_request())

    sent = transport.sent_requests[0]
    assert sent.method == "GET"
    assert sent.url == "https://app.ticketmaster.com/discovery/v2/events.json"
    assert sent.query_params["city"] == "New York"
    assert sent.query_params["startDateTime"] == "2026-08-07T00:00:00Z"
    assert sent.query_params["endDateTime"] == "2026-08-22T23:59:59Z"
    assert sent.query_params["keyword"] == "soccer"
    assert sent.query_params["apikey"] == "consumer-key-for-test"
    assert "Authorization" not in sent.headers
    assert "X-API-Key" not in sent.headers


def test_multiple_interests_keep_search_broad(monkeypatch):
    monkeypatch.setenv(_KEY_ENV, "consumer-key-for-test")
    transport = FakeTransport.always_returning(200, _body())
    provider = TicketmasterEventProvider(transport=transport)
    provider.execute(_request(interests=["fashion", "soccer"]))
    assert "keyword" not in transport.sent_requests[0].query_params


def test_live_response_maps_to_canonical_event_shape(monkeypatch):
    monkeypatch.setenv(_KEY_ENV, "consumer-key-for-test")
    provider = TicketmasterEventProvider(
        transport=FakeTransport.always_returning(200, _body(_event()))
    )
    result = provider.execute(_request())

    assert result.status == ProviderStatus.AVAILABLE
    assert result.confidence == 0.9
    assert result.source_metadata["raw_event_count"] == 1
    option = result.data[0]
    assert option["destination"] == "New York"
    assert option["name"] == "New York City FC"
    assert option["category"] == "SPORT"
    assert option["starts_at"] == "2026-08-15T23:30:00Z"
    assert option["availability_status"] == "ON_SALE"
    assert option["ticket_url"].startswith("https://")
    assert option["source_name"] == "Ticketmaster Discovery API"
    assert option["evidence_level"] == "LIVE"
    assert {"soccer", "football", "sport", "match"} <= set(option["tags"])


def test_missing_embedded_events_is_a_valid_empty_search(monkeypatch):
    monkeypatch.setenv(_KEY_ENV, "consumer-key-for-test")
    provider = TicketmasterEventProvider(
        transport=FakeTransport.always_returning(200, {"page": {"totalElements": 0}})
    )
    assert provider.execute(_request()).data == []


def test_partial_mapping_failure_preserves_good_events(monkeypatch):
    monkeypatch.setenv(_KEY_ENV, "consumer-key-for-test")
    provider = TicketmasterEventProvider(
        transport=FakeTransport.always_returning(
            200,
            _body(_event(), {"id": "broken"}),
        )
    )
    result = provider.execute(_request())
    assert len(result.data) == 1
    assert result.warnings == ["1 of 2 event(s) failed to map and were skipped"]


def test_all_mapping_failures_raise_response_error(monkeypatch):
    monkeypatch.setenv(_KEY_ENV, "consumer-key-for-test")
    provider = TicketmasterEventProvider(
        transport=FakeTransport.always_returning(200, _body({"id": "broken"}))
    )
    with pytest.raises(ProviderResponseError):
        provider.execute(_request())


def test_unsafe_ticket_url_is_not_exposed(monkeypatch):
    monkeypatch.setenv(_KEY_ENV, "consumer-key-for-test")
    provider = TicketmasterEventProvider(
        transport=FakeTransport.always_returning(
            200,
            _body(_event(url="javascript:alert(1)")),
        )
    )
    assert provider.execute(_request()).data[0]["ticket_url"] is None


def test_missing_key_fails_without_echoing_a_value():
    provider = TicketmasterEventProvider(transport=FakeTransport())
    with pytest.raises(Exception) as exc_info:
        provider.execute(_request())
    message = str(exc_info.value)
    assert "TICKETMASTER_API_KEY" in message
    assert "apikey=" not in message


def test_invalid_date_is_not_sent(monkeypatch):
    monkeypatch.setenv(_KEY_ENV, "consumer-key-for-test")
    transport = FakeTransport()
    provider = TicketmasterEventProvider(transport=transport)
    with pytest.raises(ProviderValidationError):
        provider.execute(_request(start_date="August 7"))
    assert transport.sent_requests == []


def test_ticketmaster_http_errors_use_standard_safe_types(monkeypatch):
    monkeypatch.setenv(_KEY_ENV, "consumer-key-for-test")
    provider = TicketmasterEventProvider(
        transport=FakeTransport.always_returning(401, {"fault": {}})
    )
    with pytest.raises(ProviderAuthenticationError):
        provider.execute(_request())
