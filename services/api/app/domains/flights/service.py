from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor
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

        if config.flight_provider_mode != "MOCK":
            # Validate before any Duffel call is made (T-038, section 3) —
            # MOCK mode is intentionally exempt; see live_search_validator's
            # module docstring for why.
            minors = request.minors or len(request.minor_ages)
            validate_live_flight_search(
                origin=origin,
                destination=destination,
                departure_date=request.departure_date,
                return_date=request.return_date,
                adults=request.adults,
                minors=minors,
                minor_ages=request.minor_ages,
                cabin_class=request.cabin_class,
            )

        output = flight_intelligence.recommend(
            origin=origin,
            destination=destination,
            departure_date=request.departure_date,
            return_date=request.return_date,
            cabin_class=request.cabin_class,
            adults=request.adults,
            minor_ages=request.minor_ages,
            budget_style=request.budget_style,
            airline_preference=request.airline_preference,
            trip_duration_days=duration_days,
            profile=profile,
            goal=goal,
        )

        if (
            config.flight_provider_mode != "MOCK"
            and not output["flight_options"]
            and request.departure_date
            and request.return_date
        ):
            split_option = _best_split_ticket_option(
                origin=origin,
                destination=destination,
                departure_date=request.departure_date,
                return_date=request.return_date,
                cabin_class=request.cabin_class,
                adults=request.adults,
                minor_ages=request.minor_ages,
            )
            if split_option:
                output["flight_options"] = [split_option]
                output["data_source"] = "DUFFEL_LIVE_SPLIT_TICKET"
                output["provider_status"] = "AVAILABLE"
                output["results_count"] = 1
                output["summary"] = (
                    f"No single through fare was found. A separate-ticket route via "
                    f"{split_option['split_gateway']} is available, subject to mandatory "
                    "self-transfer safeguards."
                )
                output["assumptions"] = [
                    *output["assumptions"],
                    "The displayed total combines two independently priced return tickets; it is not one protected through booking.",
                ]
                output["next_actions"] = [
                    "Allow a long connection or overnight stop in both directions.",
                    "Confirm transit and entry requirements for the self-transfer country.",
                    "Recheck baggage, terminals, minimum connection time and both fares immediately before payment.",
                    *output["next_actions"],
                ]

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
        minor_ages = _minor_ages_from_entities(entities, travellers)
        declared_minors = int(
            entities.get("children")
            or travellers.get("children")
            or 0
        ) + int(
            entities.get("infants")
            or travellers.get("infants")
            or 0
        )
        if declared_minors == 0 and minor_ages:
            declared_minors = len(minor_ages)
        request = RecommendFlightsRequest(
            traveller_id=traveller_id,
            trip_id=trip_id,
            origin=entities.get("origin") or prefs.get("home_airport", "London"),
            destination=entities.get("destination", ""),
            departure_date=entities.get("start_date"),
            return_date=entities.get("end_date"),
            cabin_class=entities.get("cabin_class") or prefs.get("cabin_class", "economy"),
            budget_style=prefs.get("budget_style", "balanced"),
            airline_preference=(
                entities.get("airline_preferences", "").split(",")[0]
                or prefs.get("preferred_airline")
            ),
            adults=int(entities.get("adults") or travellers.get("adults") or 1),
            minors=declared_minors,
            minor_ages=minor_ages,
            trip_duration_days=(trip or {}).get("duration_days", 7),
        )
        return self.recommend(request, trip=trip, goal=goal, profile=profile)


_repository = FlightRepository()
flight_intelligence_service = FlightIntelligenceService(_repository)


_SPLIT_TICKET_GATEWAYS = ("LHR", "FRA", "MAD", "AMS")


def _best_split_ticket_option(
    *,
    origin: str,
    destination: str,
    departure_date: str,
    return_date: str,
    cabin_class: str,
    adults: int,
    minor_ages: list[int],
) -> dict[str, Any] | None:
    """Find the cheapest viable pair of independent return tickets.

    This is discovery only. The combined result intentionally has no provider
    offer ID and therefore cannot be booked as a single Duffel order.
    """
    from ai.discovery.flights.flight_intelligence import FlightIntelligence
    from travelos.intelligence_gateway.discovery_adapters import GatewayFlightProvider

    def search_gateway(gateway: str) -> tuple[str, dict, dict] | None:
        first = FlightIntelligence(provider=GatewayFlightProvider()).recommend(
            origin=origin,
            destination=gateway,
            departure_date=departure_date,
            return_date=return_date,
            cabin_class=cabin_class,
            adults=adults,
            minor_ages=minor_ages,
        )["flight_options"]
        if not first:
            return None
        second = FlightIntelligence(provider=GatewayFlightProvider()).recommend(
            origin=gateway,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            cabin_class=cabin_class,
            adults=adults,
            minor_ages=minor_ages,
        )["flight_options"]
        if not second:
            return None
        a, b = first[0], second[0]
        if a["currency"] != b["currency"]:
            return None
        return gateway, a, b

    with ThreadPoolExecutor(max_workers=len(_SPLIT_TICKET_GATEWAYS)) as pool:
        candidates = [
            result
            for result in pool.map(search_gateway, _SPLIT_TICKET_GATEWAYS)
            if result is not None
        ]
    if not candidates:
        return None

    gateway, first, second = min(
        candidates,
        key=lambda item: item[1]["estimated_price"] + item[2]["estimated_price"],
    )
    total = round(first["estimated_price"] + second["estimated_price"], 2)
    mandatory_risks = [
        "SEPARATE TICKETS: the airlines do not protect the onward journey if the first flight is delayed or cancelled.",
        "SELF-TRANSFER: collect and re-check baggage, pass immigration/security where required, and change terminals independently.",
        "MISSED-CONNECTION RISK: use a long buffer or overnight stop; buying a replacement flight may be necessary.",
        "TRANSIT RULES: verify visa, transit and entry requirements for the gateway country for every traveller.",
    ]
    return {
        "airline": f"{first['airline']} + {second['airline']}",
        "flight_number": f"{first['flight_number']} / {second['flight_number']}",
        "cabin_class": cabin_class,
        "stops": first["stops"] + second["stops"] + 1,
        "layover_duration": "Long buffer or overnight self-transfer required",
        "departure_time": first["departure_time"],
        "arrival_time": second["arrival_time"],
        "total_duration": "Varies by self-transfer buffer",
        "estimated_price": total,
        "currency": first["currency"],
        "baggage_included": first["baggage_included"] and second["baggage_included"],
        "refundability": "separate_fare_rules",
        "flexibility": "separate_fare_rules",
        "departure_date": departure_date,
        "return_date": return_date,
        "match_score": 0.45,
        "reasoning": (
            f"No single through fare was available. This combines independent return tickets "
            f"{origin}–{gateway} and {gateway}–{destination}; the price is the sum of both live fares."
        ),
        "risks": mandatory_risks,
        "assumptions": [
            "This is a planning fallback, not one protected itinerary.",
            "Both component fares must be re-priced and booked separately.",
        ],
        "recommendation_type": "BEST_AVAILABLE_SPLIT_TICKET",
        "provider_offer_id": None,
        "data_source": "DUFFEL_LIVE_SPLIT_TICKET",
        "split_gateway": gateway,
    }


def _minor_ages_from_entities(
    entities: dict[str, str], travellers: dict[str, Any]
) -> list[int]:
    raw = entities.get("minor_ages")
    if raw is None:
        raw = travellers.get("minor_ages") or travellers.get("child_ages")
    if isinstance(raw, list):
        return [int(age) for age in raw]
    if not raw:
        return []
    return [int(age.strip()) for age in str(raw).split(",") if age.strip()]
