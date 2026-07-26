from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EventOption:
    event_option_id: str
    traveller_id: str | None
    trip_id: str | None
    destination: str
    name: str
    category: str
    venue_area: str
    description: str
    starts_at: str | None
    ends_at: str | None
    date_status: str
    availability_status: str
    ticket_url: str | None
    requires_ticket: bool
    team_level: str
    interests_matched: list[str]
    match_score: float
    reasoning: str
    risks: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    recommendation_type: str = "BEST_OVERALL"
    data_source: str = "TRALVANA_CURATED_EVENT_IDEAS"
    provider_status: str = "AVAILABLE"
    retrieved_at: str | None = None
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_option_id": self.event_option_id,
            "traveller_id": self.traveller_id,
            "trip_id": self.trip_id,
            "destination": self.destination,
            "name": self.name,
            "category": self.category,
            "venue_area": self.venue_area,
            "description": self.description,
            "starts_at": self.starts_at,
            "ends_at": self.ends_at,
            "date_status": self.date_status,
            "availability_status": self.availability_status,
            "ticket_url": self.ticket_url,
            "requires_ticket": self.requires_ticket,
            "team_level": self.team_level,
            "interests_matched": self.interests_matched,
            "match_score": self.match_score,
            "reasoning": self.reasoning,
            "risks": self.risks,
            "assumptions": self.assumptions,
            "recommendation_type": self.recommendation_type,
            "data_source": self.data_source,
            "provider_status": self.provider_status,
            "retrieved_at": self.retrieved_at,
            "created_at": self.created_at,
        }
