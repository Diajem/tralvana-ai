"""Deterministic event-idea provider.

The records below are deliberately *not* date-specific events. They are
curated search ideas that prove the EVENTS capability and public contract
without inventing a fixture, fashion calendar, ticket, price, or availability.
A later live provider can implement the same ``search`` method and populate
those fields with current data.
"""

from __future__ import annotations

from typing import Any


_IDEA_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "name": "Professional soccer or football match",
        "category": "SPORT",
        "venue_area": "Local stadium district",
        "description": (
            "Check the destination's official league and club fixture calendars "
            "for a home match during the trip."
        ),
        "tags": ["soccer", "football", "sport", "match"],
        "requires_ticket": True,
    },
    {
        "name": "Fashion show, exhibition, or designer event",
        "category": "FASHION",
        "venue_area": "Main fashion and design district",
        "description": (
            "Check official fashion-week, museum, gallery, and designer listings "
            "for a dated event during the trip."
        ),
        "tags": ["fashion", "style", "design", "shopping"],
        "requires_ticket": True,
    },
    {
        "name": "Food festival or guided dining experience",
        "category": "FOOD",
        "venue_area": "Central dining district",
        "description": (
            "Check current food-festival calendars and bookable local dining "
            "experiences for the travel dates."
        ),
        "tags": ["food", "dining", "restaurants", "festival"],
        "requires_ticket": False,
    },
    {
        "name": "Major cultural performance or exhibition",
        "category": "CULTURE",
        "venue_area": "Central arts district",
        "description": (
            "Check official theatre, museum, music, and cultural venue listings "
            "for the travel dates."
        ),
        "tags": ["culture", "music", "theatre", "art", "major attractions"],
        "requires_ticket": True,
    },
)


class MockEventProvider:
    """Return curated event-search ideas for any named destination."""

    def search(
        self,
        destination: str,
        start_date: str | None = None,
        end_date: str | None = None,
        interests: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        if not destination.strip():
            return []

        return [
            {
                **template,
                "destination": destination.strip(),
                "start_date": start_date,
                "end_date": end_date,
                "requested_interests": list(interests or []),
                "starts_at": None,
                "ends_at": None,
                "availability_status": "UNKNOWN",
                "ticket_url": None,
                "source_name": "Tralvana curated event ideas",
            }
            for template in _IDEA_TEMPLATES
        ]
