from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AccommodationType(str, Enum):
    HOTEL = "HOTEL"
    APARTMENT = "APARTMENT"
    HOSTEL = "HOSTEL"
    VILLA = "VILLA"
    RESORT = "RESORT"
    SERVICED_APARTMENT = "SERVICED_APARTMENT"
    BOUTIQUE_HOTEL = "BOUTIQUE_HOTEL"
    GUESTHOUSE = "GUESTHOUSE"


class RecommendationType(str, Enum):
    BEST_OVERALL = "BEST_OVERALL"
    BEST_VALUE = "BEST_VALUE"
    BEST_LOCATION = "BEST_LOCATION"
    BEST_COMFORT = "BEST_COMFORT"
    BEST_FOR_FAMILY = "BEST_FOR_FAMILY"
    BEST_FOR_BUSINESS = "BEST_FOR_BUSINESS"
    BEST_BUDGET = "BEST_BUDGET"
    AVOID = "AVOID"


@dataclass
class AccommodationOption:
    accommodation_option_id: str
    traveller_id: str | None
    trip_id: str | None
    destination: str
    property_name: str
    accommodation_type: str
    star_rating: int
    neighbourhood: str
    distance_to_centre: float
    distance_to_transport: float
    nightly_price: float
    total_price: float
    currency: str
    breakfast_included: bool
    cancellation_policy: str
    accessibility_features: list[str]
    family_friendly: bool
    business_friendly: bool
    review_score: float
    safety_score: float
    comfort_score: float
    location_score: float
    match_score: float
    reasoning: str
    risks: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    recommendation_type: str = RecommendationType.BEST_OVERALL.value
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "accommodation_option_id": self.accommodation_option_id,
            "traveller_id": self.traveller_id,
            "trip_id": self.trip_id,
            "destination": self.destination,
            "property_name": self.property_name,
            "accommodation_type": self.accommodation_type,
            "star_rating": self.star_rating,
            "neighbourhood": self.neighbourhood,
            "distance_to_centre": self.distance_to_centre,
            "distance_to_transport": self.distance_to_transport,
            "nightly_price": self.nightly_price,
            "total_price": self.total_price,
            "currency": self.currency,
            "breakfast_included": self.breakfast_included,
            "cancellation_policy": self.cancellation_policy,
            "accessibility_features": self.accessibility_features,
            "family_friendly": self.family_friendly,
            "business_friendly": self.business_friendly,
            "review_score": self.review_score,
            "safety_score": self.safety_score,
            "comfort_score": self.comfort_score,
            "location_score": self.location_score,
            "match_score": self.match_score,
            "reasoning": self.reasoning,
            "risks": self.risks,
            "assumptions": self.assumptions,
            "recommendation_type": self.recommendation_type,
            "created_at": self.created_at,
        }
