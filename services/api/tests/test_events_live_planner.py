"""T-056 live Event Intelligence acceptance through the complete planner."""

from __future__ import annotations

from datetime import date

from ai.discovery.events.event_intelligence import event_intelligence
from travelos.intelligence_gateway.discovery_adapters import GatewayEventProvider
from travelos.intelligence_gateway.gateway import IntelligenceGateway
from travelos.intelligence_gateway.provider_registry import ProviderRegistry
from travelos.intelligence_gateway.provider_status import ProviderEnvironment
from travelos.live_providers.adapters.ticketmaster_event_provider import (
    register_ticketmaster_event_provider,
)
from travelos.live_providers.transport import FakeTransport, TransportResponse


def _event(event_id: str, name: str, local_date: str) -> dict:
    return {
        "id": event_id,
        "name": name,
        "url": f"https://www.ticketmaster.com/event/{event_id}",
        "dates": {
            "start": {
                "localDate": local_date,
                "dateTime": f"{local_date}T23:00:00Z",
            },
            "status": {"code": "onsale"},
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
                    "name": "Test Stadium",
                    "city": {"name": "New York"},
                }
            ]
        },
    }


def _install_live_event_provider(monkeypatch) -> FakeTransport:
    monkeypatch.setenv("TICKETMASTER_API_KEY", "consumer-key-for-test")
    senior = _event(
        "senior",
        "New York City FC vs Inter Miami CF",
        "2026-08-12",
    )
    reserve = _event(
        "reserve",
        "NYCFC II vs Toronto FC II",
        "2026-08-10",
    )

    def responder(request):
        keyword = request.query_params.get("keyword")
        body = (
            {
                "_embedded": {"events": [reserve, senior]},
                "page": {"totalElements": 2},
            }
            if keyword in {"soccer", "football"}
            else {"page": {"totalElements": 0}}
        )
        return TransportResponse(status_code=200, body=body)

    transport = FakeTransport(responder=responder)
    registry = ProviderRegistry()
    register_ticketmaster_event_provider(transport=transport, registry=registry)
    gateway = IntelligenceGateway(
        registry=registry,
        environment=ProviderEnvironment.PRODUCTION,
    )
    monkeypatch.setattr(
        event_intelligence,
        "_provider",
        GatewayEventProvider(gateway=gateway),
    )
    monkeypatch.setattr(
        event_intelligence,
        "_today_provider",
        lambda: date(2026, 7, 26),
    )
    return transport


def test_new_york_planner_prefers_senior_event_and_preserves_live_grounding(
    client,
    monkeypatch,
):
    transport = _install_live_event_provider(monkeypatch)

    response = client.post(
        "/planner/plan",
        json={
            "message": (
                "Plan a 15-day holiday to New York with my partner from 7 August "
                "to 22 August 2026. We are travelling from Leeds but do not mind "
                "flying from Manchester or London. We are both British nationals. "
                "We love to dine out and stay in an average hotel. She loves fashion "
                "and I like soccer and places of significant interest."
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    itinerary = body["itinerary"]
    assert itinerary is not None
    assert len(itinerary["daily_outline"]) == 15

    events = itinerary["event_recommendations"]
    assert [event["name"] for event in events] == [
        "New York City FC vs Inter Miami CF",
        "NYCFC II vs Toronto FC II",
    ]
    assert events[0]["recommendation_type"] == "BEST_OVERALL"
    assert events[0]["team_level"] == "SENIOR_OR_OPEN"
    assert events[1]["team_level"] == "RESERVE_OR_YOUTH"
    assert all(event["data_source"] == "TICKETMASTER_DISCOVERY_API" for event in events)
    assert all(event["ticket_url"].startswith("https://") for event in events)
    assert all(
        "2026-08-07" <= event["starts_at"][:10] <= "2026-08-22"
        for event in events
    )

    event_notice = next(
        notice
        for notice in itinerary["grounding_notices"]
        if notice["domain"] == "events"
    )
    assert event_notice["level"] == "LIVE"
    assert event_notice["is_current"] is True
    assert event_notice["data_source"] == "TICKETMASTER_DISCOVERY_API"
    assert "fashion" in {
        request.query_params.get("keyword")
        for request in transport.sent_requests
    }
