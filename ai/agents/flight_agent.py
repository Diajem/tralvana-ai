from typing import Any

from ai.shared.agent_context import AgentContext
from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus


class FlightAgent:
    """
    Handles flight search and recommendations.
    Sprint 1: mock output with structured placeholders.
    Sprint 4+: live search via flight aggregator API.
    """

    name = "flight_agent"

    def __init__(self, context: AgentContext) -> None:
        self.context = context

    async def run(self, input_data: dict[str, Any]) -> AgentResult:
        destination = input_data.get("destination", "")
        date_hint = input_data.get("dates", {}).get("hint", "")

        if not destination:
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.NEEDS_INFORMATION,
                confidence=0.0,
                missing_information=["Destination is required to search flights."],
            )

        prefs: dict[str, Any] = {}
        if self.context.traveller_profile:
            prefs = self.context.traveller_profile.get("preferences", {})

        cabin = prefs.get("cabin_class", "economy")
        seat = prefs.get("seat", "no_preference")
        home_airport = prefs.get("home_airport", "Not set")
        meal = prefs.get("meal", "standard")

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.SUCCESS,
            confidence=0.6,
            data={
                "origin": home_airport,
                "destination": destination,
                "date_hint": date_hint or "Not specified",
                "cabin_class": cabin,
                "seat_preference": seat,
                "meal_preference": meal,
                "options": "pending_live_data",
                "note": "Live flight search activates in Sprint 4.",
            },
            assumptions=[
                f"Departing from home airport: {home_airport}.",
                f"Cabin preference: {cabin}.",
            ],
            recommendations=[
                "Confirm exact travel dates for accurate pricing.",
                "Booking 6–8 weeks ahead typically gives the best fares.",
            ],
            risks=["Prices change in real time — mock data is indicative only."],
            next_actions=["confirm_travel_dates", "search_live_flights"],
        )
