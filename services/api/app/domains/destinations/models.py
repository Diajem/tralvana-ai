from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DestinationType(str, Enum):
    CITY = "CITY"
    NEIGHBOURHOOD = "NEIGHBOURHOOD"
    ATTRACTION = "ATTRACTION"
    MUSEUM = "MUSEUM"
    FOOD_DISTRICT = "FOOD_DISTRICT"
    FOOTBALL_VENUE = "FOOTBALL_VENUE"
    SHOPPING_DISTRICT = "SHOPPING_DISTRICT"
    BEACH = "BEACH"
    NATURE_AREA = "NATURE_AREA"
    HISTORIC_SITE = "HISTORIC_SITE"
    TRANSPORT_HUB = "TRANSPORT_HUB"
    NIGHTLIFE_AREA = "NIGHTLIFE_AREA"


class RecommendationType(str, Enum):
    BEST_OVERALL = "BEST_OVERALL"
    BEST_FOR_FOOD = "BEST_FOR_FOOD"
    BEST_FOR_FOOTBALL = "BEST_FOR_FOOTBALL"
    BEST_FOR_CULTURE = "BEST_FOR_CULTURE"
    BEST_FOR_FAMILY = "BEST_FOR_FAMILY"
    BEST_FOR_BUDGET = "BEST_FOR_BUDGET"
    BEST_FOR_PHOTOGRAPHY = "BEST_FOR_PHOTOGRAPHY"
    BEST_HIDDEN_GEM = "BEST_HIDDEN_GEM"
    AVOID = "AVOID"


@dataclass
class DestinationOption:
    destination_option_id: str
    traveller_id: str | None
    trip_id: str | None
    city: str
    country: str
    region: str
    neighbourhood: str
    destination_type: str
    name: str
    description: str
    best_for: list[str]
    interests_matched: list[str]
    distance_from_centre: float
    transport_access_score: float
    food_score: float
    culture_score: float
    football_score: float
    nightlife_score: float
    family_score: float
    safety_score: float
    budget_score: float
    season_score: float
    match_score: float
    reasoning: str
    risks: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    recommendation_type: str = RecommendationType.BEST_OVERALL.value
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "destination_option_id": self.destination_option_id,
            "traveller_id": self.traveller_id,
            "trip_id": self.trip_id,
            "city": self.city,
            "country": self.country,
            "region": self.region,
            "neighbourhood": self.neighbourhood,
            "destination_type": self.destination_type,
            "name": self.name,
            "description": self.description,
            "best_for": self.best_for,
            "interests_matched": self.interests_matched,
            "distance_from_centre": self.distance_from_centre,
            "transport_access_score": self.transport_access_score,
            "food_score": self.food_score,
            "culture_score": self.culture_score,
            "football_score": self.football_score,
            "nightlife_score": self.nightlife_score,
            "family_score": self.family_score,
            "safety_score": self.safety_score,
            "budget_score": self.budget_score,
            "season_score": self.season_score,
            "match_score": self.match_score,
            "reasoning": self.reasoning,
            "risks": self.risks,
            "assumptions": self.assumptions,
            "recommendation_type": self.recommendation_type,
            "created_at": self.created_at,
        }
