from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyseWeatherRequest(BaseModel):
    traveller_id: str | None = None
    trip_id: str | None = None
    destination: str
    month_of_travel: int | None = Field(default=None, ge=1, le=12)  # omit to find the best month
    goal_type: str | None = None


class AlternativeMonth(BaseModel):
    month: int
    month_name: str
    weather_status: str
    weather_suitability_score: float


class WeatherAssessmentResponse(BaseModel):
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
    risks: list[str]
    assumptions: list[str]
    confidence: float
    weather_status: str
    alternative_months: list[AlternativeMonth]
    recommendation: str
    explanation: str
    created_at: str
