"""Traveller domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TravellerProfile:
    """A traveller's stable identity and planning preferences."""

    id: str
    created_at: str
    updated_at: str
    identity: dict[str, Any]
    preferences: dict[str, Any]
    loyalty: dict[str, Any]
    travel_history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return the existing public profile representation."""
        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "identity": dict(self.identity),
            "preferences": dict(self.preferences),
            "loyalty": dict(self.loyalty),
            "travel_history": list(self.travel_history),
        }
