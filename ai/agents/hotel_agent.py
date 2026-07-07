from typing import Any

from ai.shared.agent_context import AgentContext
from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus


class HotelAgent:
    """
    Handles hotel search and accommodation recommendations.
    Sprint 1: structured mock output using traveller preferences.
    Sprint 4+: live search via hotel aggregator API.
    """

    name = "hotel_agent"

    def __init__(self, context: AgentContext) -> None:
        self.context = context

    async def run(self, input_data: dict[str, Any]) -> AgentResult:
        destination = input_data.get("destination", "")

        prefs: dict[str, Any] = {}
        if self.context.traveller_profile:
            prefs = self.context.traveller_profile.get("preferences", {})

        accommodation_type = prefs.get("accommodation_type", "hotel")
        hotel_prefs = prefs.get("hotel_preferences", [])
        accessibility = prefs.get("accessibility_needs", [])
        budget_style = prefs.get("budget_style", "balanced")

        notes: list[str] = []
        if hotel_prefs:
            notes.append(f"Filtering for: {', '.join(hotel_prefs)}.")
        if accessibility:
            notes.append(f"Accessibility requirements: {', '.join(accessibility)}.")

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.SUCCESS,
            confidence=0.6,
            data={
                "destination": destination,
                "accommodation_type": accommodation_type,
                "hotel_preferences": hotel_prefs,
                "accessibility_needs": accessibility,
                "budget_style": budget_style,
                "options": "pending_live_data",
                "personalisation_notes": notes,
                "note": "Live hotel search activates in Sprint 4.",
            },
            assumptions=[
                f"Accommodation type preference: {accommodation_type}.",
                f"Budget style applied: {budget_style}.",
            ],
            recommendations=[
                "Confirm travel dates to check live availability.",
                "Book accommodation early for peak travel periods.",
            ],
            risks=["Availability changes daily — live search required for final booking."],
            next_actions=["confirm_hotel_dates", "search_live_hotels"],
        )
