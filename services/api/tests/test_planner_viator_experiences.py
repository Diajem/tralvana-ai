from __future__ import annotations

import asyncio
from types import SimpleNamespace

from app.domains.experiences.service import experience_discovery_service
from app.routers.planner import _attach_viator_experiences


def _itinerary() -> SimpleNamespace:
    return SimpleNamespace(
        trip_brief={
            "destination": "London",
            "start_date": "2026-10-10",
            "end_date": "2026-10-12",
            "budget": {"currency": "GBP"},
            "airport_transfer_requested": False,
        },
        experience_recommendations=[],
        transfer_recommendations=[],
        grounding_notices=[],
        modules_used=[],
        modules_unavailable=[],
    )


def test_planner_attaches_read_only_viator_sandbox_products(monkeypatch):
    captured = {}

    def search(**kwargs):
        captured.update(kwargs)
        return {
            "products": [
                {
                    "provider": "VIATOR",
                    "product_reference": "LON-123",
                    "title": "London tour",
                    "booking_enabled": False,
                    "service_type": "EXPERIENCE",
                }
            ],
            "retrieved_at": "2026-09-14T04:00:00Z",
        }

    monkeypatch.setattr(experience_discovery_service, "search", search)
    itinerary = _itinerary()

    asyncio.run(_attach_viator_experiences(itinerary))

    assert captured == {
        "destination": "London",
        "start_date": "2026-10-10",
        "end_date": "2026-10-12",
        "currency": "GBP",
        "count": 12,
    }
    assert itinerary.experience_recommendations[0]["booking_enabled"] is False
    assert itinerary.modules_used == ["viator_experiences"]
    assert itinerary.grounding_notices[0].level == "SANDBOX"
    assert itinerary.grounding_notices[0].requires_confirmation is True


def test_planner_still_loads_when_viator_is_unavailable(monkeypatch):
    def search(**_kwargs):
        raise ValueError("destination is not available")

    monkeypatch.setattr(experience_discovery_service, "search", search)
    itinerary = _itinerary()

    asyncio.run(_attach_viator_experiences(itinerary))

    assert itinerary.experience_recommendations == []
    assert itinerary.grounding_notices == []
    assert itinerary.modules_unavailable == ["viator_experiences"]


def test_requested_transfer_is_separated_from_things_to_do(monkeypatch):
    def search(**kwargs):
        assert kwargs["count"] == 50
        return {
            "products": [
                {
                    "provider": "VIATOR",
                    "product_reference": "TRF-1",
                    "title": "Private airport transfer to Ocho Rios",
                    "service_type": "TRANSFER",
                    "booking_enabled": False,
                },
                {
                    "provider": "VIATOR",
                    "product_reference": "TOUR-1",
                    "title": "Dunn's River Falls family tour",
                    "service_type": "EXPERIENCE",
                    "booking_enabled": False,
                },
            ],
            "retrieved_at": "2026-09-25T04:00:00Z",
        }

    monkeypatch.setattr(experience_discovery_service, "search", search)
    itinerary = _itinerary()
    itinerary.trip_brief["destination"] = "Ocho Rios"
    itinerary.trip_brief["airport_transfer_requested"] = True

    asyncio.run(_attach_viator_experiences(itinerary))

    assert [item["product_reference"] for item in itinerary.transfer_recommendations] == ["TRF-1"]
    assert [item["product_reference"] for item in itinerary.experience_recommendations] == ["TOUR-1"]
