"""
DemoService — end-to-end TravelOS pipeline demo.

Runs a fixed "Japan Football & Food" scenario through every layer of the stack:
  Traveller → DNA Inference → Goal → Goal Reasoning → Knowledge Graph
  → Conversation → Trip Planning

No external APIs, no database, no bookings.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Hardcoded demo scenario
# ---------------------------------------------------------------------------

_DEMO_TRAVELLER_ID = "demo-traveller-001"

_DEMO_PROFILE: dict[str, Any] = {
    "id": _DEMO_TRAVELLER_ID,
    "identity": {
        "name": "Alex Okafor",
        "nationality": "GB",
        "nationality_iso": "GB",
        "home_city": "Manchester",
    },
    "preferences": {
        "budget_style": "balanced",
        "cabin_class": "economy",
        "travel_interests": ["sport", "food_drink", "culture", "nature"],
        "accommodation_type": "hotel",
        "meal": "standard",
    },
    "loyalty": {"airline_programs": []},
}

_DEMO_GOAL = {
    "traveller_id": _DEMO_TRAVELLER_ID,
    "title": "Football & Food Tour — Japan",
    "goal_type": "FOOTBALL_TRAVEL",
    "priority": 1,
    "budget": {"min_usd": 2000, "max_usd": 2500, "currency": "GBP"},
    "timeframe": {
        "earliest": "2026-10-01",
        "latest": "2026-10-31",
        "duration_days": 10,
        "flexible": True,
    },
    "travellers": {"adults": 2, "children": 0, "infants": 0},
    "interests": ["football", "food", "photography"],
    "success_criteria": [
        "Find and confirm an official FC Tokyo fixture at Ajinomoto Stadium",
        "Experience authentic ramen and sushi in Tokyo",
        "Visit Senso-ji Temple for photography",
    ],
    "constraints": [
        "Maximum budget £2,000 per person",
        "Economy class travel only",
    ],
    "flexibility": {"dates": True, "duration": False, "budget": False},
}

_DEMO_CONVERSATION_MSG = (
    "I need to plan a trip to Tokyo in October — 10 days, football and food, "
    "two adults, balanced budget."
)


class DemoService:
    """
    Orchestrates the full TravelOS pipeline for the demo scenario.
    Every run gets isolated Goal, Trip, and conversation-session stores.
    """

    async def run(self) -> dict[str, Any]:
        from ai.concierge.conversation_engine import ConversationEngine
        from ai.concierge.session_store import InMemorySessionStore
        from ai.trip_brain.context import ContextBuilder
        from ai.trip_brain.coordinator import TripBrain
        from app.adapters.planning_adapter import PlanningAdapter
        from app.domains.goals.repository import GoalRepository
        from app.domains.goals.service import GoalService
        from app.domains.trips.repository import TripRepository
        from app.domains.trips.service import TripPlanningService

        generated_at = datetime.now(timezone.utc).isoformat()
        goal_service = GoalService(GoalRepository())
        trip_service = TripPlanningService(
            TripRepository(),
            goal_service=goal_service,
        )
        planning_port = PlanningAdapter(
            goal_service=goal_service,
            trip_planning_service=trip_service,
        )
        conversation_engine = ConversationEngine(
            store=InMemorySessionStore(),
            planning_port=planning_port,
            brain=TripBrain(ContextBuilder(planning_port=planning_port)),
        )

        # ── Stage 1: DNA inference ─────────────────────────────────────────
        dna_section = self._run_dna()

        # ── Stage 2: Goal ─────────────────────────────────────────────────
        goal = self._run_goal(goal_service)

        # ── Stage 3: Goal reasoning ────────────────────────────────────────
        reasoning = self._run_goal_reasoning(goal)

        # ── Stage 4: Knowledge graph insights ─────────────────────────────
        kg_insights = self._run_knowledge()

        # ── Stage 5: Conversation engine ──────────────────────────────────
        conversation = await self._run_conversation(conversation_engine)

        # ── Stage 6: Trip planning ─────────────────────────────────────────
        trip = self._run_trip(goal["goal_id"], goal_service, trip_service)
        trip_section = self._trip_section(trip)

        # ── Stage 7: Pipeline summary ──────────────────────────────────────
        overall_conf = trip_section["confidence"]

        return {
            "demo_id": "japan-football-food",
            "generated_at": generated_at,
            "traveller": self._traveller_section(),
            "dna": dna_section,
            "goal": self._goal_section(goal, reasoning),
            "conversation": conversation,
            "knowledge_insights": kg_insights,
            "trip_plan": trip_section,
            "pipeline_summary": {
                "stages_completed": 7,
                "overall_confidence": overall_conf,
                "pipeline": [
                    "Traveller Profile Built",
                    "DNA Inferred",
                    "Goal Created",
                    "Goal Reasoned",
                    "Knowledge Graph Queried",
                    "Conversation Processed",
                    "Trip Plan Generated",
                ],
                "data_sources": [
                    "In-memory knowledge graph (199 nodes, 205 edges)",
                    "TravellerDNA inference (12 archetypes)",
                    "GoalReasoner (deterministic scoring)",
                    "TripPlanner + ItineraryBuilder (planning outline)",
                    "Traveller-declared GBP budget (not supplier prices)",
                    "Readiness checks for dates, prices, and fixtures",
                ],
            },
        }

    # ------------------------------------------------------------------
    # Stage implementations
    # ------------------------------------------------------------------

    def _run_dna(self) -> dict[str, Any]:
        from ai.intelligence import dna_inference_service
        from ai.intelligence.traveller_dna.dna_types import DNA_DESCRIPTIONS
        dna = dna_inference_service.infer(_DEMO_PROFILE)
        description = DNA_DESCRIPTIONS.get(dna.primary_type, "")
        top_traits = sorted(dna.traits.items(), key=lambda x: x[1], reverse=True)[:5]
        return {
            "primary_type": dna.primary_type,
            "secondary_types": dna.secondary_types,
            "confidence": dna.confidence,
            "top_traits": {k: round(v, 2) for k, v in top_traits},
            "all_traits": {k: round(v, 2) for k, v in dna.traits.items()},
            "description": description,
            "inferred_at": dna.inferred_at,
        }

    def _run_goal(self, goal_service: Any) -> dict[str, Any]:
        from app.domains.goals.schemas import (
            BudgetSchema, CreateGoalRequest, FlexibilitySchema,
            TimeframeSchema, TravellersSchema,
        )
        t = _DEMO_GOAL["timeframe"]
        b = _DEMO_GOAL["budget"]
        tr = _DEMO_GOAL["travellers"]
        f = _DEMO_GOAL["flexibility"]

        req = CreateGoalRequest(
            traveller_id=_DEMO_TRAVELLER_ID,
            title=_DEMO_GOAL["title"],
            goal_type=_DEMO_GOAL["goal_type"],
            priority=_DEMO_GOAL["priority"],
            budget=BudgetSchema(
                min_usd=b["min_usd"], max_usd=b["max_usd"], currency=b["currency"]
            ),
            timeframe=TimeframeSchema(
                earliest=t["earliest"],
                latest=t["latest"],
                duration_days=t["duration_days"],
                flexible=t["flexible"],
            ),
            travellers=TravellersSchema(
                adults=tr["adults"], children=tr["children"], infants=tr["infants"]
            ),
            interests=_DEMO_GOAL["interests"],
            success_criteria=_DEMO_GOAL["success_criteria"],
            constraints=_DEMO_GOAL["constraints"],
            flexibility=FlexibilitySchema(**f),
        )
        return goal_service.create(req)

    def _run_goal_reasoning(self, goal: dict[str, Any]) -> dict[str, Any]:
        from ai.goals.goal_reasoner import goal_reasoner
        return goal_reasoner.reason(goal)

    def _run_knowledge(self) -> dict[str, Any]:
        from ai.intelligence import knowledge_service
        city = knowledge_service.find_entity("City", "Tokyo")
        country = knowledge_service.find_entity("Country", "Japan")

        if not city:
            return {"destination_city": "Tokyo", "country": "Japan", "note": "Not in graph"}

        airports = knowledge_service.get_connected_entities(city.id, "Airport")
        attractions = knowledge_service.get_connected_entities(city.id, "Attraction")
        museums = knowledge_service.get_connected_entities(city.id, "Museum")
        restaurants = knowledge_service.get_connected_entities(city.id, "Restaurant")
        sports_venues = knowledge_service.get_connected_entities(city.id, "SportsVenue")
        football_clubs = knowledge_service.get_connected_entities(city.id, "FootballClub")
        events = knowledge_service.get_connected_entities(city.id, "Event")
        weather = knowledge_service.get_connected_entities(city.id, "Weather")
        transport = knowledge_service.get_connected_entities(city.id, "Transport")

        return {
            "destination_city": city.name,
            "country": country.name if country else "Japan",
            "continent": country.continent if country else "Asia",
            "safety_level": country.safety_level if country else "low",
            "city_population": city.population,
            "city_tags": city.tags,
            "airports": [
                {"name": a.name, "iata_code": a.iata_code, "is_international": a.is_international}
                for a in airports
            ],
            "attractions": [
                {"name": a.name, "type": a.attraction_type, "tags": a.tags}
                for a in attractions
            ],
            "museums": [
                {"name": m.name, "category": m.category, "tags": m.tags}
                for m in museums
            ],
            "restaurants": [
                {"name": r.name, "tier": r.price_tier, "tags": r.tags}
                for r in restaurants
            ],
            "sports_venues": [
                {"name": v.name, "capacity": v.capacity, "sport": v.primary_sport}
                for v in sports_venues
            ],
            "football_clubs": [
                {"name": c.name, "league": c.league, "founded": c.founded_year}
                for c in football_clubs
            ],
            "events": [
                {"name": e.name, "type": e.event_type, "month": e.month, "tags": e.tags}
                for e in events
            ],
            "weather_records": [
                {"month": w.month, "avg_temp_c": w.avg_temp_c, "condition": w.condition, "season": w.season}
                for w in weather
            ],
            "transport": [
                {"name": t.name, "type": t.transport_type}
                for t in transport
            ],
            "graph_stats": knowledge_service.get_stats(),
        }

    async def _run_conversation(self, conversation_engine: Any) -> dict[str, Any]:
        result = await conversation_engine.process(
            _DEMO_CONVERSATION_MSG,
            traveller_id=_DEMO_TRAVELLER_ID,
        )
        return {
            "message_sent": _DEMO_CONVERSATION_MSG,
            "conversation_id": result.get("conversation_id"),
            "intent": result.get("intent"),
            "response": result.get("response"),
            "confidence": result.get("confidence"),
            "assumptions": result.get("assumptions", []),
            "goal_id": result.get("goal_id"),
            "trip_id": result.get("trip_id"),
        }

    def _run_trip(
        self,
        goal_id: str,
        goal_service: Any,
        trip_planning_service: Any,
    ) -> dict[str, Any]:
        from app.domains.trips.schemas import CreateTripPlanRequest
        from app.domains.trips.schemas import TravellersSchema as TripTravellersSchema

        goal = goal_service.get(goal_id)
        req = CreateTripPlanRequest(
            traveller_id=_DEMO_TRAVELLER_ID,
            goal_id=goal_id,
            origin="Manchester",
            destination="Tokyo",
            duration_days=10,
            budget_style="balanced",
            cabin_class="economy",
            interests=["football", "food", "photography"],
            travellers=TripTravellersSchema(adults=2, children=0, infants=0),
        )
        return trip_planning_service.plan(req, goal=goal, profile=_DEMO_PROFILE)

    # ------------------------------------------------------------------
    # Response builders
    # ------------------------------------------------------------------

    def _traveller_section(self) -> dict[str, Any]:
        identity = _DEMO_PROFILE["identity"]
        prefs = _DEMO_PROFILE["preferences"]
        return {
            "traveller_id": _DEMO_TRAVELLER_ID,
            "name": identity["name"],
            "home_city": identity["home_city"],
            "nationality": identity["nationality"],
            "budget_style": prefs["budget_style"],
            "cabin_class": prefs["cabin_class"],
            "travel_interests": prefs["travel_interests"],
            "summary": (
                f"{identity['name']} is a traveller from {identity['home_city']}, {identity['nationality']}. "
                f"They prefer {prefs['budget_style']} travel in {prefs['cabin_class']} class. "
                f"Key interests: {', '.join(prefs['travel_interests'])}."
            ),
        }

    def _goal_section(
        self, goal: dict[str, Any], reasoning: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "goal_id": goal["goal_id"],
            "title": goal["title"],
            "goal_type": goal["goal_type"],
            "status": goal["status"],
            "destination": "Japan (Tokyo)",
            "duration_days": goal.get("timeframe", {}).get("duration_days", 10),
            "budget": goal.get("budget", {}),
            "travellers": goal.get("travellers", {}),
            "interests": goal.get("interests", []),
            "success_criteria": goal.get("success_criteria", []),
            "constraints": goal.get("constraints", []),
            "goal_summary": (
                f"**{goal['title']}** — {goal['goal_type'].replace('_', ' ').title()} "
                f"| Status: {goal['status']} | planning outline. "
                f"Budget: GBP {goal['budget']['min_usd']:,}–"
                f"{goal['budget']['max_usd']:,}. "
                f"Timeframe: October 2026, {goal['timeframe']['duration_days']} days. "
                f"Interests: {', '.join(goal.get('interests', []))}."
            ),
            "goal_completeness_score": reasoning["planning_readiness_score"],
            "missing_information": reasoning["missing_information"],
            "recommended_next_actions": reasoning["recommended_next_actions"],
            "suitable_agents": reasoning["suitable_agents"],
        }

    def _trip_section(self, trip: dict[str, Any]) -> dict[str, Any]:
        itinerary = [
            {
                key: value
                for key, value in day.items()
                if key != "estimated_daily_cost_usd"
            }
            for day in trip["draft_itinerary"]
        ]
        return {
            "trip_id": trip["trip_id"],
            "title": trip["title"],
            "origin": trip["origin"],
            "destination": trip["destination"],
            "duration_days": trip["duration_days"],
            "travel_style": trip["travel_style"],
            "confidence": 0.55,
            "status": "PLANNING_IN_PROGRESS",
            "trip_summary": (
                "A 10-day draft outline for Tokyo from Manchester for two adults. "
                "Current flights, accommodation, prices, and football fixtures "
                "have not yet been checked."
            ),
            "draft_itinerary": itinerary,
            "declared_budget": {
                "minimum": 2000,
                "maximum": 2500,
                "currency": "GBP",
                "assessment_status": "NOT_YET_ASSESSED",
                "source": "TRAVELLER_DECLARED",
            },
            "estimated_budget_breakdown": None,
            "risks": [
                {
                    "type": "financial",
                    "severity": "medium",
                    "description": (
                        "The GBP 2,000–2,500 budget has not been tested against "
                        "current supplier prices."
                    ),
                    "mitigation": (
                        "Search current flights and accommodation, then reconcile "
                        "all costs in GBP."
                    ),
                },
                {
                    "type": "logistics",
                    "severity": "medium",
                    "description": (
                        "October is only a broad travel window; exact departure "
                        "and return dates are not set."
                    ),
                    "mitigation": (
                        "Choose exact dates before checking availability or booking."
                    ),
                },
                {
                    "type": "events",
                    "severity": "medium",
                    "description": (
                        "No football fixture or ticket has been confirmed."
                    ),
                    "mitigation": (
                        "Check FC Tokyo and J.League official calendars for the "
                        "chosen dates."
                    ),
                },
            ],
            "assumptions": [
                "The daily outline is illustrative and requires opening-hours checks.",
                "No supplier, fare, property, or event ticket is recommended.",
            ],
            "missing_information": [
                "Exact departure and return dates",
                "Current flight and accommodation prices",
                "An official football fixture matching the chosen dates",
            ],
            "next_actions": [
                "Choose exact departure and return dates",
                "Run current flight and accommodation searches",
                "Confirm any football fixture on an official calendar",
                "Reconcile the complete trip cost in GBP before booking",
            ],
            "recommended_agents": trip["recommended_agents"],
        }


demo_service = DemoService()
