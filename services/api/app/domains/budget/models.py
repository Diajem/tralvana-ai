from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RecommendationType(str, Enum):
    BEST_OVERALL = "BEST_OVERALL"
    LOWEST_COST = "LOWEST_COST"
    MOST_COMFORTABLE = "MOST_COMFORTABLE"
    BEST_VALUE = "BEST_VALUE"
    BEST_FOR_FAMILY = "BEST_FOR_FAMILY"
    AVOID = "AVOID"


@dataclass
class BudgetOption:
    budget_option_id: str
    traveller_id: str | None
    trip_id: str | None
    destination: str
    region: str
    budget_style: str
    duration_days: int
    adults: int
    children: int
    cabin_class: str
    daily_cost_usd: int
    flight_cost_usd: int
    accommodation_usd: int
    food_usd: int
    activities_usd: int
    misc_usd: int
    total_cost_usd: int
    cost_per_day_usd: int
    cost_per_person_usd: int
    currency: str
    affordability_score: float
    comfort_score: float
    cost_certainty_score: float
    family_suitability_score: float
    match_score: float
    reasoning: str
    risks: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    recommendation_type: str = RecommendationType.BEST_OVERALL.value
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "budget_option_id": self.budget_option_id,
            "traveller_id": self.traveller_id,
            "trip_id": self.trip_id,
            "destination": self.destination,
            "region": self.region,
            "budget_style": self.budget_style,
            "duration_days": self.duration_days,
            "adults": self.adults,
            "children": self.children,
            "cabin_class": self.cabin_class,
            "daily_cost_usd": self.daily_cost_usd,
            "flight_cost_usd": self.flight_cost_usd,
            "accommodation_usd": self.accommodation_usd,
            "food_usd": self.food_usd,
            "activities_usd": self.activities_usd,
            "misc_usd": self.misc_usd,
            "total_cost_usd": self.total_cost_usd,
            "cost_per_day_usd": self.cost_per_day_usd,
            "cost_per_person_usd": self.cost_per_person_usd,
            "currency": self.currency,
            "affordability_score": self.affordability_score,
            "comfort_score": self.comfort_score,
            "cost_certainty_score": self.cost_certainty_score,
            "family_suitability_score": self.family_suitability_score,
            "match_score": self.match_score,
            "reasoning": self.reasoning,
            "risks": self.risks,
            "assumptions": self.assumptions,
            "recommendation_type": self.recommendation_type,
            "created_at": self.created_at,
        }
