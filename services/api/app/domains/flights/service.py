from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.domains.flights.models import FlightOption
from app.domains.flights.repository import FlightRepository
from app.domains.flights.schemas import RecommendFlightsRequest
from ai.discovery.flights.live_search_validator import validate_live_flight_search
from travelos.config.configuration_manager import config


class FlightIntelligenceService:
    """
    Orchestrates flight recommendation from a request, an optional Trip Plan,
    and an optional traveller profile.

    Sprint 1: deterministic mock data via ai/discovery/flights/. Sprint 4+:
    swap MockFlightProvider for a real FlightProvider (Amadeus, Skyscanner).
    """

    def __init__(self, repository: FlightRepository) -> None:
        self._repo = repository

    def recommend(
        self,
        request: RecommendFlightsRequest,
        trip: dict[str, Any] | None = None,
        goal: dict[str, Any] | None = None,
        profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from ai.discovery.flights.flight_intelligence import flight_intelligence

        origin = request.origin
        destination = request.destination
        duration_days = request.trip_duration_days
        if trip:
            origin = trip.get("origin") or origin
            destination = trip.get("destination") or destination
            duration_days = trip.get("duration_days") or duration_days

        if config.flight_provider_mode == "LIVE_SANDBOX":
            # Validate before any Duffel call is made (T-038, section 3) —
            # MOCK mode is intentionally exempt; see live_search_validator's
            # module docstring for why.
            validate_live_flight_search(
                origin=origin,
                destination=destination,
                departure_date=request.departure_date,
                return_date=request.return_date,
                adults=request.adults,
                cabin_class=request.cabin_class,
            )

        output = flight_intelligence.recommend(
            origin=origin,
            destination=destination,
            departure_date=request.departure_date,
            return_date=request.return_date,
            cabin_class=request.cabin_class,
            adults=request.adults,
            budget_style=request.budget_style,
            airline_preference=request.airline_preference,
            trip_duration_days=duration_days,
            profile=profile,
            goal=goal,
        )

        now = datetime.now(timezone.utc).isoformat()
        flights = [
            FlightOption(
                flight_option_id=str(uuid.uuid4()),
                traveller_id=request.traveller_id,
                trip_id=request.trip_id,
                origin=origin,
                destination=destination,
                departure_date=option["departure_date"],
                return_date=option["return_date"],
                airline=option["airline"],
                flight_number=option["flight_number"],
                cabin_class=option["cabin_class"],
                stops=option["stops"],
                layover_duration=option["layover_duration"],
                departure_time=option["departure_time"],
                arrival_time=option["arrival_time"],
                total_duration=option["total_duration"],
                estimated_price=option["estimated_price"],
                currency=option["currency"],
                baggage_included=option["baggage_included"],
                refundability=option["refundability"],
                flexibility=option["flexibility"],
                match_score=option["match_score"],
                reasoning=option["reasoning"],
                risks=option["risks"],
                assumptions=option["assumptions"],
                recommendation_type=option["recommendation_type"],
                created_at=now,
                provider_offer_id=option.get("provider_offer_id"),
                data_source=option.get("data_source", "MOCK"),
            )
            for option in output["flight_options"]
        ]
        self._repo.save_many(flights)

        return {
            "traveller_id": request.traveller_id,
            "trip_id": request.trip_id,
            "origin": origin,
            "destination": destination,
            "flight_options": [f.to_dict() for f in flights],
            "assumptions": output["assumptions"],
            "next_actions": output["next_actions"],
            "recommended_agents": output["recommended_agents"],
            "summary": output["summary"],
            "data_source": output.get("data_source", "MOCK"),
            "retrieved_at": output.get("retrieved_at", ""),
            "provider_status": output.get("provider_status", "AVAILABLE"),
            "results_count": output.get("results_count", len(flights)),
            "request_id": output.get("request_id", ""),
        }

    def get(self, flight_option_id: str) -> dict[str, Any] | None:
        flight = self._repo.get(flight_option_id)
        return flight.to_dict() if flight else None

    def list_by_trip(self, trip_id: str) -> list[dict[str, Any]]:
        return [f.to_dict() for f in self._repo.list_by_trip(trip_id)]

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
        request = RecommendFlightsRequest(
            traveller_id=traveller_id,
            trip_id=trip_id,
            origin=entities.get("origin") or prefs.get("home_airport", "London"),
            destination=entities.get("destination", ""),
            departure_date=entities.get("start_date"),
            return_date=entities.get("end_date"),
            cabin_class=prefs.get("cabin_class", "economy"),
            budget_style=prefs.get("budget_style", "balanced"),
            adults=int(entities.get("adults") or travellers.get("adults") or 1),
            trip_duration_days=(trip or {}).get("duration_days", 7),
        )
        return self.recommend(request, trip=trip, goal=goal, profile=profile)


_repository = FlightRepository()
flight_intelligence_service = FlightIntelligenceService(_repository)
