from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.domains.budget.models import BudgetOption
from app.domains.budget.repository import BudgetRepository
from app.domains.budget.schemas import RecommendBudgetRequest


class BudgetIntelligenceService:
    """
    Orchestrates budget recommendation from a request, an optional Trip
    Plan, and an optional Goal (for the budget cap) and traveller profile.

    Sprint 1: deterministic mock regional rates via ai/discovery/budget/.
    Sprint 4+: swap MockBudgetProvider for a real pricing feed.
    """

    def __init__(self, repository: BudgetRepository) -> None:
        self._repo = repository

    def recommend(
        self,
        request: RecommendBudgetRequest,
        trip: dict[str, Any] | None = None,
        goal: dict[str, Any] | None = None,
        profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from ai.discovery.budget.budget_intelligence import budget_intelligence

        destination = request.destination
        duration_days = request.duration_days
        adults = request.adults
        children = request.children
        if trip:
            destination = destination or trip.get("destination")
            duration_days = trip.get("duration_days") or duration_days

        goal_type = request.goal_type or (goal or {}).get("goal_type")

        output = budget_intelligence.recommend(
            destination=destination,
            duration_days=duration_days,
            adults=adults,
            children=children,
            budget_style=request.budget_style,
            profile=profile,
            goal={"goal_type": goal_type, "budget": (goal or {}).get("budget")} if goal or goal_type else goal,
        )

        now = datetime.now(timezone.utc).isoformat()
        options = [
            BudgetOption(
                budget_option_id=str(uuid.uuid4()),
                traveller_id=request.traveller_id,
                trip_id=request.trip_id,
                destination=option["destination"],
                region=option["region"],
                budget_style=option["budget_style"],
                duration_days=option["duration_days"],
                adults=option["adults"],
                children=option["children"],
                cabin_class=option["cabin_class"],
                daily_cost_usd=option["daily_cost_usd"],
                flight_cost_usd=option["flight_cost_usd"],
                accommodation_usd=option["accommodation_usd"],
                food_usd=option["food_usd"],
                activities_usd=option["activities_usd"],
                misc_usd=option["misc_usd"],
                total_cost_usd=option["total_cost_usd"],
                cost_per_day_usd=option["cost_per_day_usd"],
                cost_per_person_usd=option["cost_per_person_usd"],
                currency=option["currency"],
                affordability_score=option["affordability_score"],
                comfort_score=option["comfort_score"],
                cost_certainty_score=option["cost_certainty_score"],
                family_suitability_score=option["family_suitability_score"],
                match_score=option["match_score"],
                reasoning=option["reasoning"],
                risks=option["risks"],
                assumptions=option["assumptions"],
                recommendation_type=option["recommendation_type"],
                created_at=now,
            )
            for option in output["budget_options"]
        ]
        self._repo.save_many(options)

        return {
            "traveller_id": request.traveller_id,
            "trip_id": request.trip_id,
            "destination": destination,
            "budget_options": [o.to_dict() for o in options],
            "assumptions": output["assumptions"],
            "next_actions": output["next_actions"],
            "recommended_agents": output["recommended_agents"],
            "summary": output["summary"],
        }

    def get(self, budget_option_id: str) -> dict[str, Any] | None:
        option = self._repo.get(budget_option_id)
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
        travellers = (trip or {}).get("travellers", {})
        request = RecommendBudgetRequest(
            traveller_id=traveller_id,
            trip_id=trip_id,
            destination=entities.get("destination") or None,
            budget_style=prefs.get("budget_style", "balanced"),
            duration_days=(trip or {}).get("duration_days", 7),
            adults=int(entities.get("adults") or travellers.get("adults") or 1),
            children=int(entities.get("children") or travellers.get("children") or 0),
        )
        return self.recommend(request, trip=trip, goal=goal, profile=profile)


_repository = BudgetRepository()
budget_intelligence_service = BudgetIntelligenceService(_repository)
