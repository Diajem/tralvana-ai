from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RecommendationType(str, Enum):
    BEST_OVERALL = "BEST_OVERALL"
    LOWEST_PRICE = "LOWEST_PRICE"
    SHORTEST_DURATION = "SHORTEST_DURATION"
    BEST_FOR_FAMILY = "BEST_FOR_FAMILY"
    BEST_FOR_BUSINESS = "BEST_FOR_BUSINESS"
    BEST_FOR_COMFORT = "BEST_FOR_COMFORT"
    BEST_FOR_BUDGET = "BEST_FOR_BUDGET"
    AVOID = "AVOID"


@dataclass
class FlightOption:
    flight_option_id: str
    traveller_id: str | None
    trip_id: str | None
    origin: str
    destination: str
    departure_date: str
    return_date: str | None
    airline: str
    flight_number: str
    cabin_class: str
    stops: int
    layover_duration: str
    departure_time: str
    arrival_time: str
    total_duration: str
    estimated_price: float
    currency: str
    baggage_included: bool
    refundability: str
    flexibility: str
    match_score: float
    reasoning: str
    risks: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    recommendation_type: str = RecommendationType.BEST_OVERALL.value
    created_at: str = ""
    # Preserved for future booking work only (T-038 explicitly excludes
    # booking) — deliberately NOT included in to_dict()'s public shape;
    # see docs/LIVE_FLIGHT_SEARCH.md's "Provider Offer Identifiers" section.
    provider_offer_id: str | None = None
    # Safe provenance label (T-038) — MOCK | DUFFEL_SANDBOX | MOCK_FALLBACK.
    # Public (unlike provider_offer_id above) so a single flight fetched
    # via GET /flights/{id} still carries its own sandbox/mock label.
    data_source: str = "MOCK"

    def to_dict(self) -> dict:
        return {
            "flight_option_id": self.flight_option_id,
            "traveller_id": self.traveller_id,
            "trip_id": self.trip_id,
            "origin": self.origin,
            "destination": self.destination,
            "departure_date": self.departure_date,
            "return_date": self.return_date,
            "airline": self.airline,
            "flight_number": self.flight_number,
            "cabin_class": self.cabin_class,
            "stops": self.stops,
            "layover_duration": self.layover_duration,
            "departure_time": self.departure_time,
            "arrival_time": self.arrival_time,
            "total_duration": self.total_duration,
            "estimated_price": self.estimated_price,
            "currency": self.currency,
            "baggage_included": self.baggage_included,
            "refundability": self.refundability,
            "flexibility": self.flexibility,
            "match_score": self.match_score,
            "reasoning": self.reasoning,
            "risks": self.risks,
            "assumptions": self.assumptions,
            "recommendation_type": self.recommendation_type,
            "created_at": self.created_at,
            "data_source": self.data_source,
        }
