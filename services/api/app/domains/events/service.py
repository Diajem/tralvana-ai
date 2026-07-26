from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.domains.events.models import EventOption
from app.domains.events.repository import EventRepository
from app.domains.events.schemas import RecommendEventsRequest


class EventIntelligenceService:
    def __init__(self, repository: EventRepository) -> None:
        self._repo = repository

    def recommend(
        self,
        request: RecommendEventsRequest,
        trip: dict[str, Any] | None = None,
        goal: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from ai.discovery.events.event_intelligence import event_intelligence

        destination = request.destination or (trip or {}).get("destination", "")
        interests = request.interests or (goal or {}).get("interests", [])
        start_date = (
            request.start_date.isoformat()
            if request.start_date
            else (goal or {}).get("timeframe", {}).get("earliest")
        )
        end_date = (
            request.end_date.isoformat()
            if request.end_date
            else (goal or {}).get("timeframe", {}).get("latest")
        )

        output = event_intelligence.recommend(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            interests=interests,
        )
        now = datetime.now(timezone.utc).isoformat()
        options = [
            EventOption(
                event_option_id=str(uuid.uuid4()),
                traveller_id=request.traveller_id,
                trip_id=request.trip_id,
                destination=option["destination"],
                name=option["name"],
                category=option["category"],
                venue_area=option["venue_area"],
                description=option["description"],
                starts_at=option["starts_at"],
                ends_at=option["ends_at"],
                date_status=option["date_status"],
                availability_status=option["availability_status"],
                ticket_url=option["ticket_url"],
                requires_ticket=option["requires_ticket"],
                team_level=option["team_level"],
                interests_matched=option["interests_matched"],
                match_score=option["match_score"],
                reasoning=option["reasoning"],
                risks=option["risks"],
                assumptions=option["assumptions"],
                recommendation_type=option["recommendation_type"],
                data_source=output["data_source"],
                provider_status=output["provider_status"],
                retrieved_at=output["retrieved_at"],
                created_at=now,
            )
            for option in output["event_options"]
        ]
        self._repo.save_many(options)

        return {
            "traveller_id": request.traveller_id,
            "trip_id": request.trip_id,
            "destination": destination,
            "start_date": start_date,
            "end_date": end_date,
            "event_options": [option.to_dict() for option in options],
            "data_source": output["data_source"],
            "provider_status": output["provider_status"],
            "retrieved_at": output["retrieved_at"],
            "assumptions": output["assumptions"],
            "next_actions": output["next_actions"],
            "recommended_agents": output["recommended_agents"],
            "summary": output["summary"],
            "filter_summary": output["filter_summary"],
        }

    def get(self, event_option_id: str) -> dict[str, Any] | None:
        option = self._repo.get(event_option_id)
        return option.to_dict() if option else None

    def list_by_trip(self, trip_id: str) -> list[dict[str, Any]]:
        return [option.to_dict() for option in self._repo.list_by_trip(trip_id)]

    def recommend_from_conversation(
        self,
        traveller_id: str | None,
        trip_id: str | None,
        entities: dict[str, str],
        profile: dict[str, Any] | None,
    ) -> dict[str, Any]:
        del profile  # reserved for future personalisation; no hidden inference in T-053
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

        interests = [
            value for value in entities.get("interests", "").split(",")
            if value
        ] or (goal or {}).get("interests", [])

        request = RecommendEventsRequest(
            traveller_id=traveller_id,
            trip_id=trip_id,
            destination=entities.get("destination")
            or (trip or {}).get("destination")
            or "",
            start_date=entities.get("start_date")
            or (goal or {}).get("timeframe", {}).get("earliest"),
            end_date=entities.get("end_date")
            or (goal or {}).get("timeframe", {}).get("latest"),
            interests=interests,
        )
        return self.recommend(request, trip=trip, goal=goal)


_repository = EventRepository()
event_intelligence_service = EventIntelligenceService(_repository)
