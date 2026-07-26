from __future__ import annotations

from ai.discovery.events.event_intelligence import EventIntelligence
from travelos.intelligence_gateway.discovery_adapters import GatewayEventProvider
from travelos.intelligence_gateway.gateway import IntelligenceGateway
from travelos.intelligence_gateway.provider_registry import ProviderRegistry
from travelos.intelligence_gateway.provider_status import ProviderEnvironment
from travelos.live_providers.adapters.ticketmaster_event_provider import (
    register_ticketmaster_event_provider,
)
from travelos.live_providers.transport import FakeTransport
from travelos.live_providers.transport import TransportResponse


def _response() -> dict:
    return {
        "_embedded": {
            "events": [
                {
                    "id": "evt-1",
                    "name": "New York City FC Match",
                    "url": "https://www.ticketmaster.com/event/evt-1",
                    "dates": {
                        "start": {"dateTime": "2026-08-15T23:30:00Z"},
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
                                "name": "Yankee Stadium",
                                "city": {"name": "New York"},
                            }
                        ]
                    },
                }
            ]
        },
        "page": {"totalElements": 1},
    }


def test_event_intelligence_exposes_live_provenance(monkeypatch):
    monkeypatch.setenv("TICKETMASTER_API_KEY", "consumer-key-for-test")
    registry = ProviderRegistry()
    register_ticketmaster_event_provider(
        transport=FakeTransport.always_returning(200, _response()),
        registry=registry,
    )
    gateway = IntelligenceGateway(
        registry=registry,
        environment=ProviderEnvironment.PRODUCTION,
    )
    engine = EventIntelligence(
        provider=GatewayEventProvider(gateway=gateway)
    )
    output = engine.recommend(
        destination="New York",
        start_date="2026-08-07",
        end_date="2026-08-22",
        interests=["soccer"],
    )

    assert output["data_source"] == "TICKETMASTER_DISCOVERY_API"
    assert output["provider_status"] == "AVAILABLE"
    assert output["retrieved_at"]
    assert "live event listing" in output["summary"].lower()
    option = output["event_options"][0]
    assert option["date_status"] == "CONFIRMED"
    assert option["availability_status"] == "ON_SALE"
    assert option["ticket_url"].startswith("https://")
    assert "live" in option["reasoning"].lower()
    assert "no live event calendar" not in " ".join(option["risks"]).lower()


def test_cancelled_live_event_cannot_score_like_on_sale_listing():
    from ai.discovery.events.event_scorer import EventScorer

    base = {
        "date_status": "CONFIRMED",
        "_tags": ["soccer", "sport", "match"],
    }
    scorer = EventScorer()
    on_sale = scorer.score(
        {**base, "availability_status": "ON_SALE"},
        ["soccer"],
    )
    cancelled = scorer.score(
        {**base, "availability_status": "CANCELLED"},
        ["soccer"],
    )
    assert cancelled["match_score"] < on_sale["match_score"]


def _live_event(
    *,
    event_id: str,
    name: str,
    local_date: str | None,
    date_time: str | None,
    segment: str,
    genre: str,
) -> dict:
    start = {}
    if local_date:
        start["localDate"] = local_date
    if date_time:
        start["dateTime"] = date_time
    return {
        "id": event_id,
        "name": name,
        "url": f"https://www.ticketmaster.com/event/{event_id}",
        "dates": {
            "start": start,
            "status": {"code": "onsale"},
        },
        "classifications": [
            {
                "segment": {"name": segment},
                "genre": {"name": genre},
            }
        ],
        "_embedded": {
            "venues": [
                {
                    "name": "Test Venue",
                    "city": {"name": "New York"},
                }
            ]
        },
    }


def _event_body(*events: dict) -> dict:
    return {
        "_embedded": {"events": list(events)},
        "page": {"totalElements": len(events)},
    }


def _live_engine(monkeypatch, responder, *, today=None):
    monkeypatch.setenv("TICKETMASTER_API_KEY", "consumer-key-for-test")
    transport = FakeTransport(responder=responder)
    registry = ProviderRegistry()
    register_ticketmaster_event_provider(transport=transport, registry=registry)
    gateway = IntelligenceGateway(
        registry=registry,
        environment=ProviderEnvironment.PRODUCTION,
    )
    provider = GatewayEventProvider(gateway=gateway)
    engine_kwargs = {"provider": provider}
    if today is not None:
        engine_kwargs["today_provider"] = lambda: today
    return EventIntelligence(**engine_kwargs), provider, transport


def test_multiple_interests_use_specific_queries_and_deduplicate(monkeypatch):
    shared = _live_event(
        event_id="shared",
        name="Fashion and Football Benefit",
        local_date="2026-08-15",
        date_time="2026-08-15T23:30:00Z",
        segment="Sports",
        genre="Soccer",
    )

    def responder(request):
        keyword = request.query_params["keyword"]
        specific = _live_event(
            event_id=keyword,
            name=f"{keyword.title()} event",
            local_date="2026-08-16",
            date_time="2026-08-16T20:00:00Z",
            segment="Sports" if keyword == "soccer" else "Arts & Theatre",
            genre="Soccer" if keyword == "soccer" else "Fashion",
        )
        return TransportResponse(
            status_code=200,
            body=_event_body(shared, specific),
        )

    engine, provider, transport = _live_engine(monkeypatch, responder)
    output = engine.recommend(
        destination="New York",
        start_date="2026-08-07",
        end_date="2026-08-22",
        interests=["fashion", "soccer"],
    )

    assert [request.query_params["keyword"] for request in transport.sent_requests] == [
        "fashion",
        "soccer",
    ]
    assert len(output["event_options"]) == 3
    assert len(
        {option["name"] for option in output["event_options"]}
    ) == 3
    assert provider.last_result.source_metadata["query_count"] == 2
    assert provider.last_result.source_metadata["raw_event_count"] == 4
    assert provider.last_result.source_metadata["unique_event_count"] == 3


def test_live_results_are_strictly_filtered_to_inclusive_local_travel_dates(
    monkeypatch,
):
    events = [
        _live_event(
            event_id="before",
            name="Past Soccer Match",
            local_date="2026-08-06",
            date_time="2026-08-06T23:00:00Z",
            segment="Sports",
            genre="Soccer",
        ),
        _live_event(
            event_id="start",
            name="Opening-day Soccer Match",
            local_date="2026-08-07",
            date_time="2026-08-08T00:30:00Z",
            segment="Sports",
            genre="Soccer",
        ),
        _live_event(
            event_id="end",
            name="Final-night Soccer Match",
            local_date="2026-08-22",
            # UTC is next day; localDate must win for travel-window checks.
            date_time="2026-08-23T01:00:00Z",
            segment="Sports",
            genre="Soccer",
        ),
        _live_event(
            event_id="after",
            name="Late Soccer Match",
            local_date="2026-08-23",
            date_time="2026-08-23T20:00:00Z",
            segment="Sports",
            genre="Soccer",
        ),
        _live_event(
            event_id="undated",
            name="Undated Soccer Match",
            local_date=None,
            date_time=None,
            segment="Sports",
            genre="Soccer",
        ),
    ]
    engine, _, _ = _live_engine(
        monkeypatch,
        lambda request: TransportResponse(
            status_code=200,
            body=_event_body(*events),
        ),
    )
    output = engine.recommend(
        destination="New York",
        start_date="2026-08-07",
        end_date="2026-08-22",
        interests=["soccer"],
    )

    assert {option["name"] for option in output["event_options"]} == {
        "Opening-day Soccer Match",
        "Final-night Soccer Match",
    }
    assert output["filter_summary"] == {
        "provider_result_count": 5,
        "excluded_outside_travel_dates": 3,
        "excluded_as_irrelevant": 0,
        "returned_event_count": 2,
    }


def test_unrelated_live_sports_are_removed_from_soccer_results(monkeypatch):
    events = [
        _live_event(
            event_id="basketball",
            name="New York Basketball Game",
            local_date="2026-08-10",
            date_time="2026-08-10T23:00:00Z",
            segment="Sports",
            genre="Basketball",
        ),
        _live_event(
            event_id="soccer",
            name="New York City FC Match",
            local_date="2026-08-12",
            date_time="2026-08-12T23:00:00Z",
            segment="Sports",
            genre="Soccer",
        ),
    ]
    engine, _, _ = _live_engine(
        monkeypatch,
        lambda request: TransportResponse(
            status_code=200,
            body=_event_body(*events),
        ),
    )
    output = engine.recommend(
        destination="New York",
        start_date="2026-08-07",
        end_date="2026-08-22",
        interests=["soccer"],
    )

    assert [option["name"] for option in output["event_options"]] == [
        "New York City FC Match"
    ]
    assert output["filter_summary"]["excluded_as_irrelevant"] == 1


def test_live_search_without_trip_dates_excludes_events_before_today(monkeypatch):
    from datetime import date

    events = [
        _live_event(
            event_id="past",
            name="Past Soccer Match",
            local_date="2026-07-25",
            date_time="2026-07-25T23:00:00Z",
            segment="Sports",
            genre="Soccer",
        ),
        _live_event(
            event_id="future",
            name="Future Soccer Match",
            local_date="2026-07-27",
            date_time="2026-07-27T23:00:00Z",
            segment="Sports",
            genre="Soccer",
        ),
    ]
    engine, _, _ = _live_engine(
        monkeypatch,
        lambda request: TransportResponse(
            status_code=200,
            body=_event_body(*events),
        ),
        today=date(2026, 7, 26),
    )
    output = engine.recommend(
        destination="New York",
        interests=["soccer"],
    )

    assert [option["name"] for option in output["event_options"]] == [
        "Future Soccer Match"
    ]
    assert output["filter_summary"]["excluded_outside_travel_dates"] == 1
