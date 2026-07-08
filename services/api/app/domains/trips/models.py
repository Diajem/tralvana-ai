from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TripStatus(str, Enum):
    DRAFT = "DRAFT"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"
    READY = "READY"
    ARCHIVED = "ARCHIVED"


@dataclass
class TripPlan:
    trip_id: str
    traveller_id: str | None
    goal_id: str | None
    title: str
    origin: str
    destination: str
    duration_days: int
    budget: dict                              # {min_usd, max_usd, currency}
    travellers: dict                          # {adults, children, infants}
    interests: list[str]
    travel_style: str                         # budget_style
    assumptions: list[str]
    missing_information: list[str]
    recommended_destinations: list[dict]
    draft_itinerary: list[dict]              # [{day, title, theme, morning, afternoon, evening, ...}]
    estimated_budget_breakdown: dict
    risks: list[dict]                         # [{type, severity, description, mitigation}]
    confidence: float
    status: str
    created_at: str
    updated_at: str
    recommended_agents: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    trip_summary: str = ""

    def to_dict(self) -> dict:
        return {
            "trip_id": self.trip_id,
            "traveller_id": self.traveller_id,
            "goal_id": self.goal_id,
            "title": self.title,
            "origin": self.origin,
            "destination": self.destination,
            "duration_days": self.duration_days,
            "budget": self.budget,
            "travellers": self.travellers,
            "interests": self.interests,
            "travel_style": self.travel_style,
            "assumptions": self.assumptions,
            "missing_information": self.missing_information,
            "recommended_destinations": self.recommended_destinations,
            "draft_itinerary": self.draft_itinerary,
            "estimated_budget_breakdown": self.estimated_budget_breakdown,
            "risks": self.risks,
            "confidence": self.confidence,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "recommended_agents": self.recommended_agents,
            "next_actions": self.next_actions,
            "trip_summary": self.trip_summary,
        }
