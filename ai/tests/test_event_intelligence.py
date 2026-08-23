from __future__ import annotations

from ai.discovery.events.event_intelligence import EventIntelligence
from ai.discovery.events.event_normalizer import EventNormalizer
from ai.discovery.events.event_scorer import EventScorer
from travelos.intelligence_gateway.discovery_adapters import GatewayEventProvider
from travelos.intelligence_gateway.gateway import IntelligenceGateway
from travelos.intelligence_gateway.provider_registry import ProviderRegistry
from travelos.intelligence_gateway.provider_status import Capability, ProviderEnvironment
from travelos.intelligence_gateway.discovery_adapters import register_default_providers


def _intelligence() -> EventIntelligence:
    registry = ProviderRegistry()
    register_default_providers(registry)
    gateway = IntelligenceGateway(
        registry=registry,
        environment=ProviderEnvironment.MOCK,
    )
    return EventIntelligence(provider=GatewayEventProvider(gateway=gateway))


def test_event_capability_has_a_mock_provider():
    registry = ProviderRegistry()
    register_default_providers(registry)
    names = {
        provider.provider_name
        for provider in registry.get_providers(Capability.EVENTS)
    }
    assert names == {"mock_event_provider"}


def test_new_york_fashion_and_soccer_are_ranked_as_curated_ideas():
    output = _intelligence().recommend(
        destination="New York",
        start_date="2026-08-07",
        end_date="2026-08-22",
        interests=["fashion", "soccer"],
    )
    assert output["data_source"] == "TRALVANA_CURATED_EVENT_IDEAS"
    assert output["provider_status"] == "AVAILABLE"
    assert len(output["event_options"]) == 2
    assert {
        option["category"] for option in output["event_options"]
    } == {"FASHION", "SPORT"}
    top_two = output["event_options"][:2]
    assert {option["category"] for option in top_two} == {"FASHION", "SPORT"}
    assert all(option["date_status"] == "UNVERIFIED" for option in top_two)
    assert all(option["availability_status"] == "UNKNOWN" for option in top_two)
    assert all(option["ticket_url"] is None for option in top_two)


def test_no_destination_returns_no_event_ideas():
    output = _intelligence().recommend(destination="", interests=["fashion"])
    assert output["event_options"] == []


def test_normalizer_never_promotes_missing_date_to_confirmed():
    event = EventNormalizer().normalize(
        {
            "destination": "New York",
            "name": "Fashion idea",
            "category": "fashion",
            "tags": ["fashion"],
            "starts_at": None,
        }
    )
    assert event["date_status"] == "UNVERIFIED"
    assert event["availability_status"] == "UNKNOWN"


def test_normalizer_exposes_provider_local_date_and_time():
    event = EventNormalizer().normalize(
        {
            "destination": "New York",
            "name": "Evening event",
            "starts_at": "2026-10-11T23:30:00Z",
            "_local_date": "2026-10-11",
            "_local_time": "19:30:00",
        }
    )

    assert event["local_date"] == "2026-10-11"
    assert event["local_time"] == "19:30:00"


def test_scorer_caps_strong_interest_match_when_evidence_is_unverified():
    event = {
        "date_status": "UNVERIFIED",
        "_tags": ["fashion", "style"],
    }
    score = EventScorer().score(event, ["fashion"])
    assert score["interests_matched"] == ["fashion"]
    assert score["match_score"] < 1.0


def test_output_explicitly_requires_live_confirmation():
    output = _intelligence().recommend(
        destination="New York",
        interests=["fashion"],
    )
    assert any("no live calendar" in item.lower() for item in output["assumptions"])
    assert any("official" in item.lower() for item in output["next_actions"])
    assert all(
        any("confirm" in risk.lower() for risk in option["risks"])
        for option in output["event_options"]
    )
