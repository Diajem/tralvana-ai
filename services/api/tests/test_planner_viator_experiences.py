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
        },
        experience_recommendations=[],
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
        "count": 6,
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
