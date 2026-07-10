from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.domains.weather.models import WeatherAssessment
from app.domains.weather.repository import WeatherRepository
from app.domains.weather.schemas import AnalyseWeatherRequest


class WeatherIntelligenceService:
    """
    Orchestrates a weather/safety assessment from a request, an optional
    Trip Plan (for a default destination), and an optional traveller
    profile.

    Deliberately independent of Destination and Budget Intelligence — no
    import from app.domains.destinations or app.domains.budget. Only Trip
    context (destination, goal_type) is used as a convenience default,
    matching every other Discovery module's service layer. This keeps
    Weather Intelligence consumable standalone by a future Trip Brain
    without a dependency edge into another Discovery module's internals.

    Sprint 1: deterministic mock climate profiles via ai/discovery/weather/.
    Sprint 4+: swap MockWeatherProvider for a real climate data feed.
    """

    def __init__(self, repository: WeatherRepository) -> None:
        self._repo = repository

    def analyse(
        self,
        request: AnalyseWeatherRequest,
        trip: dict[str, Any] | None = None,
        goal: dict[str, Any] | None = None,
        profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from ai.discovery.weather.weather_intelligence import weather_intelligence

        destination = request.destination
        if trip:
            destination = destination or trip.get("destination")

        goal_type = request.goal_type or (goal or {}).get("goal_type")

        output = weather_intelligence.analyse(
            destination=destination,
            month_of_travel=request.month_of_travel,
            profile=profile,
            goal={"goal_type": goal_type} if goal_type else goal,
        )

        now = datetime.now(timezone.utc).isoformat()
        assessment = WeatherAssessment(
            weather_assessment_id=str(uuid.uuid4()),
            traveller_id=request.traveller_id,
            trip_id=request.trip_id,
            destination=output["destination"],
            month_of_travel=output["month_of_travel"],
            season=output["season"],
            average_temperature=output["average_temperature"],
            rainfall_level=output["rainfall_level"],
            humidity_level=output["humidity_level"],
            daylight_hours=output["daylight_hours"],
            weather_summary=output["weather_summary"],
            weather_suitability_score=output["weather_suitability_score"],
            outdoor_activity_score=output["outdoor_activity_score"],
            photography_score=output["photography_score"],
            family_score=output["family_score"],
            transport_disruption_risk=output["transport_disruption_risk"],
            natural_hazard_risk=output["natural_hazard_risk"],
            health_risk=output["health_risk"],
            personal_suitability=output["personal_suitability"],
            packing_recommendations=output["packing_recommendations"],
            safety_summary=output["safety_summary"],
            risks=output["risks"],
            assumptions=output["assumptions"],
            confidence=output["confidence"],
            weather_status=output["weather_status"],
            alternative_months=output["alternative_months"],
            recommendation=output["recommendation"],
            explanation=output["explanation"],
            created_at=now,
        )
        self._repo.save(assessment)
        return assessment.to_dict()

    def get(self, weather_assessment_id: str) -> dict[str, Any] | None:
        assessment = self._repo.get(weather_assessment_id)
        return assessment.to_dict() if assessment else None

    def list_by_trip(self, trip_id: str) -> list[dict[str, Any]]:
        return [a.to_dict() for a in self._repo.list_by_trip(trip_id)]

    def analyse_from_conversation(
        self,
        traveller_id: str | None,
        trip_id: str | None,
        entities: dict[str, str],
        profile: dict[str, Any] | None,
    ) -> dict[str, Any]:
        trip: dict[str, Any] | None = None
        goal: dict[str, Any] | None = None
        if trip_id:
            try:
                from app.domains.trips.service import trip_planning_service
                trip = trip_planning_service.get(trip_id)
                if trip and trip.get("goal_id"):
                    from app.domains.goals.service import goal_service
                    goal = goal_service.get(trip["goal_id"])
            except Exception:
                pass

        month_raw = entities.get("month")
        request = AnalyseWeatherRequest(
            traveller_id=traveller_id,
            trip_id=trip_id,
            destination=entities.get("destination") or (trip or {}).get("destination") or "",
            month_of_travel=int(month_raw) if month_raw else None,
        )
        return self.analyse(request, trip=trip, goal=goal, profile=profile)


_repository = WeatherRepository()
weather_intelligence_service = WeatherIntelligenceService(_repository)
