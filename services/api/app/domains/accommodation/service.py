from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.domains.accommodation.models import AccommodationOption
from app.domains.accommodation.repository import AccommodationRepository
from app.domains.accommodation.schemas import RecommendAccommodationRequest
from ai.discovery.accommodation.live_search_validator import validate_live_accommodation_search
from travelos.config.configuration_manager import config


class AccommodationIntelligenceService:
    """
    Orchestrates accommodation recommendation from a request, an optional
    Trip Plan, and an optional traveller profile.

    Sprint 1: deterministic mock data via ai/discovery/accommodation/.
    Sprint 4+: swap MockAccommodationProvider for a real AccommodationProvider
    (Booking.com, Expedia).
    """

    def __init__(self, repository: AccommodationRepository) -> None:
        self._repo = repository

    def recommend(
        self,
        request: RecommendAccommodationRequest,
        trip: dict[str, Any] | None = None,
        goal: dict[str, Any] | None = None,
        profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from ai.discovery.accommodation.accommodation_intelligence import accommodation_intelligence

        destination = request.destination
        nights = request.nights
        if trip:
            destination = trip.get("destination") or destination
            nights = trip.get("duration_days") or nights

        if config.accommodation_provider_mode == "LIVE_SANDBOX":
            # Validate before any Duffel Stays call is made (T-039,
            # section 4) — MOCK mode is intentionally exempt; see
            # live_search_validator's module docstring for why.
            validate_live_accommodation_search(
                destination=destination,
                check_in_date=request.check_in_date,
                nights=nights,
                adults=request.adults,
                rooms=request.rooms,
            )

        output = accommodation_intelligence.recommend(
            destination=destination,
            check_in_date=request.check_in_date,
            nights=nights,
            accommodation_type_preference=request.accommodation_type,
            budget_style=request.budget_style,
            adults=request.adults,
            children=request.children,
            rooms=request.rooms,
            business_trip=request.business_trip,
            accessibility_required=request.accessibility_required,
            profile=profile,
            goal=goal,
        )

        now = datetime.now(timezone.utc).isoformat()
        options = [
            AccommodationOption(
                accommodation_option_id=str(uuid.uuid4()),
                traveller_id=request.traveller_id,
                trip_id=request.trip_id,
                destination=destination,
                property_name=option["property_name"],
                accommodation_type=option["accommodation_type"],
                star_rating=option["star_rating"],
                neighbourhood=option["neighbourhood"],
                distance_to_centre=option["distance_to_centre"],
                distance_to_transport=option["distance_to_transport"],
                nightly_price=option["nightly_price"],
                total_price=option["total_price"],
                currency=option["currency"],
                breakfast_included=option["breakfast_included"],
                cancellation_policy=option["cancellation_policy"],
                accessibility_features=option["accessibility_features"],
                family_friendly=option["family_friendly"],
                business_friendly=option["business_friendly"],
                review_score=option["review_score"],
                safety_score=option["safety_score"],
                comfort_score=option["comfort_score"],
                location_score=option["location_score"],
                match_score=option["match_score"],
                reasoning=option["reasoning"],
                risks=option["risks"],
                assumptions=option["assumptions"],
                recommendation_type=option["recommendation_type"],
                created_at=now,
                provider_property_id=option.get("provider_property_id"),
                provider_rate_id=option.get("provider_rate_id"),
                data_source=option.get("data_source", "MOCK"),
            )
            for option in output["accommodation_options"]
        ]
        self._repo.save_many(options)

        return {
            "traveller_id": request.traveller_id,
            "trip_id": request.trip_id,
            "destination": destination,
            "accommodation_options": [o.to_dict() for o in options],
            "assumptions": output["assumptions"],
            "next_actions": output["next_actions"],
            "recommended_agents": output["recommended_agents"],
            "summary": output["summary"],
            "data_source": output.get("data_source", "MOCK"),
            "provider_status": output.get("provider_status", "AVAILABLE"),
            "retrieved_at": output.get("retrieved_at", ""),
            "request_id": output.get("request_id", ""),
            "raw_results_count": output.get("raw_results_count", 0),
            "normalised_results_count": output.get("normalised_results_count", len(options)),
            "ranked_results_count": output.get("ranked_results_count", len(options)),
        }

    def get(self, accommodation_option_id: str) -> dict[str, Any] | None:
        option = self._repo.get(accommodation_option_id)
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
        request = RecommendAccommodationRequest(
            traveller_id=traveller_id,
            trip_id=trip_id,
            destination=entities.get("destination", ""),
            budget_style=prefs.get("budget_style", "balanced"),
            nights=(trip or {}).get("duration_days", 7),
        )
        return self.recommend(request, trip=trip, goal=goal, profile=profile)


_repository = AccommodationRepository()
accommodation_intelligence_service = AccommodationIntelligenceService(_repository)
