from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.domains.destinations.models import DestinationOption
from app.domains.destinations.repository import DestinationRepository
from app.domains.destinations.schemas import RecommendDestinationsRequest


class DestinationIntelligenceService:
    """
    Orchestrates destination recommendation from a request, an optional
    Trip Plan, and an optional traveller profile.

    Sprint 1: deterministic mock data via ai/discovery/destinations/.
    Sprint 4+: swap MockDestinationProvider for a real DestinationProvider
    (Google Places or similar).
    """

    def __init__(self, repository: DestinationRepository) -> None:
        self._repo = repository

    def recommend(
        self,
        request: RecommendDestinationsRequest,
        trip: dict[str, Any] | None = None,
        goal: dict[str, Any] | None = None,
        profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from ai.discovery.destinations.destination_intelligence import destination_intelligence

        city = request.city
        interests = request.interests
        duration_days = request.trip_duration_days
        if trip:
            city = city or trip.get("destination")
            interests = interests or trip.get("interests", [])
            duration_days = trip.get("duration_days") or duration_days

        goal_type = request.goal_type or (goal or {}).get("goal_type")

        output = destination_intelligence.recommend(
            city=city,
            interests=interests,
            budget_style=request.budget_style,
            travel_month=request.travel_month,
            trip_duration_days=duration_days,
            has_children=request.children > 0,
            profile=profile,
            goal={"goal_type": goal_type} if goal_type else goal,
        )

        now = datetime.now(timezone.utc).isoformat()
        options = [
            DestinationOption(
                destination_option_id=str(uuid.uuid4()),
                traveller_id=request.traveller_id,
                trip_id=request.trip_id,
                city=option["city"],
                country=option["country"],
                region=option["region"],
                neighbourhood=option["neighbourhood"],
                destination_type=option["destination_type"],
                name=option["name"],
                description=option["description"],
                best_for=option["best_for"],
                interests_matched=option["interests_matched"],
                distance_from_centre=option["distance_from_centre"],
                transport_access_score=option["transport_access_score"],
                food_score=option["food_score"],
                culture_score=option["culture_score"],
                football_score=option["football_score"],
                nightlife_score=option["nightlife_score"],
                family_score=option["family_score"],
                safety_score=option["safety_score"],
                budget_score=option["budget_score"],
                season_score=option["season_score"],
                match_score=option["match_score"],
                reasoning=option["reasoning"],
                risks=option["risks"],
                assumptions=option["assumptions"],
                recommendation_type=option["recommendation_type"],
                created_at=now,
            )
            for option in output["destination_options"]
        ]
        self._repo.save_many(options)

        return {
            "traveller_id": request.traveller_id,
            "trip_id": request.trip_id,
            "city": city,
            "destination_options": [o.to_dict() for o in options],
            "assumptions": output["assumptions"],
            "next_actions": output["next_actions"],
            "recommended_agents": output["recommended_agents"],
            "summary": output["summary"],
        }

    def get(self, destination_option_id: str) -> dict[str, Any] | None:
        option = self._repo.get(destination_option_id)
        return option.to_dict() if option else None

    def list_by_trip(self, trip_id: str) -> list[dict[str, Any]]:
        return [o.to_dict() for o in self._repo.list_by_trip(trip_id)]

    def recommend_from_conversation(
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

        prefs = (profile or {}).get("preferences", {})
        request = RecommendDestinationsRequest(
            traveller_id=traveller_id,
            trip_id=trip_id,
            city=entities.get("destination") or None,
            interests=prefs.get("travel_interests", []),
            budget_style=prefs.get("budget_style", "balanced"),
            trip_duration_days=(trip or {}).get("duration_days", 7),
        )
        return self.recommend(request, trip=trip, goal=goal, profile=profile)


_repository = DestinationRepository()
destination_intelligence_service = DestinationIntelligenceService(_repository)
