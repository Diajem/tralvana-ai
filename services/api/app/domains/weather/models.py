from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class WeatherStatus(str, Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    ACCEPTABLE = "ACCEPTABLE"
    CHALLENGING = "CHALLENGING"
    NOT_RECOMMENDED = "NOT_RECOMMENDED"


@dataclass
class WeatherAssessment:
    weather_assessment_id: str
    traveller_id: str | None
    trip_id: str | None
    destination: str
    month_of_travel: int
    season: str
    average_temperature: float | None
    rainfall_level: str
    humidity_level: str
    daylight_hours: float | None
    weather_summary: str
    weather_suitability_score: float
    outdoor_activity_score: float
    photography_score: float
    family_score: float
    transport_disruption_risk: str
    natural_hazard_risk: str
    health_risk: str
    personal_suitability: str
    packing_recommendations: list[str]
    safety_summary: str
    confidence: float
    weather_status: str
    risks: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    alternative_months: list[dict] = field(default_factory=list)
    recommendation: str = ""
    explanation: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "weather_assessment_id": self.weather_assessment_id,
            "traveller_id": self.traveller_id,
            "trip_id": self.trip_id,
            "destination": self.destination,
            "month_of_travel": self.month_of_travel,
            "season": self.season,
            "average_temperature": self.average_temperature,
            "rainfall_level": self.rainfall_level,
            "humidity_level": self.humidity_level,
            "daylight_hours": self.daylight_hours,
            "weather_summary": self.weather_summary,
            "weather_suitability_score": self.weather_suitability_score,
            "outdoor_activity_score": self.outdoor_activity_score,
            "photography_score": self.photography_score,
            "family_score": self.family_score,
            "transport_disruption_risk": self.transport_disruption_risk,
            "natural_hazard_risk": self.natural_hazard_risk,
            "health_risk": self.health_risk,
            "personal_suitability": self.personal_suitability,
            "packing_recommendations": self.packing_recommendations,
            "safety_summary": self.safety_summary,
            "risks": self.risks,
            "assumptions": self.assumptions,
            "confidence": self.confidence,
            "weather_status": self.weather_status,
            "alternative_months": self.alternative_months,
            "recommendation": self.recommendation,
            "explanation": self.explanation,
            "created_at": self.created_at,
        }
