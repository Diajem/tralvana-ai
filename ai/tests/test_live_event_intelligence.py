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
