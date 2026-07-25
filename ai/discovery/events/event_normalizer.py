from __future__ import annotations

from typing import Any


class EventNormalizer:
    """Translate provider-shaped records into the canonical event contract."""

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        starts_at = raw.get("starts_at")
        return {
            "destination": raw["destination"],
            "name": raw["name"],
            "category": str(raw.get("category", "OTHER")).upper(),
            "venue_area": raw.get("venue_area", ""),
            "description": raw.get("description", ""),
            "starts_at": starts_at,
            "ends_at": raw.get("ends_at"),
            "date_status": "CONFIRMED" if starts_at else "UNVERIFIED",
            "availability_status": raw.get("availability_status", "UNKNOWN"),
            "ticket_url": raw.get("ticket_url"),
            "requires_ticket": bool(raw.get("requires_ticket", False)),
            "source_name": raw.get("source_name", "Unknown event source"),
            "_tags": [str(tag).lower() for tag in raw.get("tags", [])],
            "_requested_interests": [
                str(interest).lower()
                for interest in raw.get("requested_interests", [])
            ],
        }


event_normalizer = EventNormalizer()
