"""FastAPI/domain-service implementation of the AI PlanningPort."""

from __future__ import annotations

from typing import Any


class PlanningAdapter:
    def create_goal(
        self,
        traveller_id: str | None,
        message: str,
        entities: dict[str, str],
    ) -> dict[str, Any]:
        from app.domains.goals.service import goal_service

        return goal_service.create_from_conversation(traveller_id, message, entities)

    def create_trip(
        self,
        traveller_id: str | None,
        goal_id: str | None,
        entities: dict[str, str],
        profile: dict[str, Any] | None,
    ) -> dict[str, Any]:
        from app.domains.trips.service import trip_planning_service

        return trip_planning_service.plan_from_conversation(
            traveller_id=traveller_id,
            goal_id=goal_id,
            entities=entities,
            profile=profile,
        )

    def get_goal(self, goal_id: str) -> dict[str, Any] | None:
        from app.domains.goals.service import goal_service

        return goal_service.get(goal_id)

    def get_trip(self, trip_id: str) -> dict[str, Any] | None:
        from app.domains.trips.service import trip_planning_service

        return trip_planning_service.get(trip_id)

    def recommend_flights(self, **kwargs: Any) -> dict[str, Any]:
        from app.domains.flights.service import flight_intelligence_service

        return flight_intelligence_service.recommend_from_conversation(**kwargs)

    def recommend_accommodation(self, **kwargs: Any) -> dict[str, Any]:
        from app.domains.accommodation.service import accommodation_intelligence_service

        return accommodation_intelligence_service.recommend_from_conversation(**kwargs)

    def recommend_destinations(self, **kwargs: Any) -> dict[str, Any]:
        from app.domains.destinations.service import destination_intelligence_service

        return destination_intelligence_service.recommend_from_conversation(**kwargs)

    def recommend_budget(self, **kwargs: Any) -> dict[str, Any]:
        from app.domains.budget.service import budget_intelligence_service

        return budget_intelligence_service.recommend_from_conversation(**kwargs)

    def check_visa(self, **kwargs: Any) -> dict[str, Any]:
        from app.domains.visa.service import visa_intelligence_service

        return visa_intelligence_service.check_from_conversation(**kwargs)

    def analyse_weather(self, **kwargs: Any) -> dict[str, Any]:
        from app.domains.weather.service import weather_intelligence_service

        return weather_intelligence_service.analyse_from_conversation(**kwargs)

    def recommend_events(self, **kwargs: Any) -> dict[str, Any]:
        from app.domains.events.service import event_intelligence_service

        return event_intelligence_service.recommend_from_conversation(**kwargs)
