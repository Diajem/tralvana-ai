from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.domains.trips.models import TripPlan, TripStatus
from app.domains.trips.repository import TripRepository
from app.domains.trips.schemas import CreateTripPlanRequest, UpdateTripPlanRequest


class TripPlanningService:
    """
    Orchestrates trip plan creation from a request, a Goal, and a traveller profile.

    Sprint 1: deterministic in-memory planning via ai/planning/.
    Sprint 3+: swap repository for DB; upgrade planners with live data.
    """

    def __init__(self, repository: TripRepository) -> None:
        self._repo = repository

    def plan(
        self,
        request: CreateTripPlanRequest,
        goal: dict[str, Any] | None = None,
        profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from ai.planning.trip_planner import TripPlanner
        planner = TripPlanner()

        # Merge goal fields into planning params
        destination = request.destination
        if not destination and goal:
            destination = self._extract_destination(goal)

        interests = request.interests or (goal.get("interests", []) if goal else [])
        duration = request.duration_days
        if goal and not duration:
            duration = goal.get("timeframe", {}).get("duration_days") or 7

        goal_type = (goal or {}).get("goal_type", "GENERAL_TRAVEL")
        travellers = request.travellers.model_dump()
        if goal and not any(request.travellers.model_dump().values()):
            travellers = goal.get("travellers", {"adults": 1, "children": 0, "infants": 0})

        output = planner.plan(
            origin=request.origin,
            destination=destination,
            duration_days=duration,
            budget_style=request.budget_style,
            cabin_class=request.cabin_class,
            interests=interests,
            travellers=travellers,
            goal_type=goal_type,
            goal=goal,
            profile=profile,
        )

        # Determine status
        status = TripStatus.READY.value if output["confidence"] >= 0.65 else \
                 TripStatus.NEEDS_INFORMATION.value if output["missing_information"] else \
                 TripStatus.DRAFT.value

        now = datetime.now(timezone.utc).isoformat()
        title = self._generate_title(destination, duration, goal_type)

        trip = TripPlan(
            trip_id=str(uuid.uuid4()),
            traveller_id=request.traveller_id,
            goal_id=request.goal_id,
            title=title,
            origin=request.origin,
            destination=destination or "TBD",
            duration_days=duration,
            budget=goal.get("budget", {"min_usd": None, "max_usd": None, "currency": "USD"}) if goal
                   else {"min_usd": None, "max_usd": None, "currency": "USD"},
            travellers=travellers,
            interests=interests,
            travel_style=request.budget_style,
            assumptions=output["assumptions"],
            missing_information=output["missing_information"],
            recommended_destinations=output["recommended_destinations"],
            draft_itinerary=output["draft_itinerary"],
            estimated_budget_breakdown=output["estimated_budget_breakdown"],
            risks=output["risks"],
            confidence=output["confidence"],
            status=status,
            created_at=now,
            updated_at=now,
            recommended_agents=output["recommended_agents"],
            next_actions=output["next_actions"],
            trip_summary=output["trip_summary"],
        )
        self._repo.save(trip)
        return trip.to_dict()

    def get(self, trip_id: str) -> dict[str, Any] | None:
        trip = self._repo.get(trip_id)
        return trip.to_dict() if trip else None

    def list_by_traveller(self, traveller_id: str) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self._repo.list_by_traveller(traveller_id)]

    def update(self, trip_id: str, request: UpdateTripPlanRequest) -> dict[str, Any] | None:
        updates = {k: v for k, v in request.model_dump(exclude_none=True).items()}
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        trip = self._repo.update(trip_id, updates)
        return trip.to_dict() if trip else None

    def plan_from_conversation(
        self,
        traveller_id: str | None,
        goal_id: str | None,
        entities: dict[str, str],
        profile: dict[str, Any] | None,
    ) -> dict[str, Any]:
        goal: dict[str, Any] | None = None
        if goal_id:
            try:
                from app.domains.goals.service import goal_service
                goal = goal_service.get(goal_id)
            except Exception:
                pass

        prefs = (profile or {}).get("preferences", {})
        origin = prefs.get("home_airport", "London")
        destination = entities.get("destination", "")
        budget_style = prefs.get("budget_style", "balanced")
        cabin_class = prefs.get("cabin_class", "economy")
        interests = goal.get("interests", []) if goal else []
        duration = goal.get("timeframe", {}).get("duration_days") if goal else 7

        request = CreateTripPlanRequest(
            traveller_id=traveller_id,
            goal_id=goal_id,
            origin=origin,
            destination=destination,
            duration_days=duration or 7,
            budget_style=budget_style,
            cabin_class=cabin_class,
            interests=interests,
        )
        return self.plan(request, goal=goal, profile=profile)

    # ------------------------------------------------------------------

    def _extract_destination(self, goal: dict) -> str:
        title = goal.get("title", "")
        for marker in ("to ", "in ", "at "):
            idx = title.lower().find(marker)
            if idx != -1:
                candidate = title[idx + len(marker):].strip().split()[0].rstrip(".,")
                if len(candidate) > 2:
                    return candidate.title()
        return ""

    def _generate_title(self, destination: str, duration: int, goal_type: str) -> str:
        type_label = goal_type.replace("_", " ").title()
        dest = destination or "Unknown Destination"
        return f"{type_label} — {dest} ({duration} days)"


_repository = TripRepository()
trip_planning_service = TripPlanningService(_repository)
