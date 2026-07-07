from typing import Any

from ai.agents.base_agent import AgentContext, AgentResult, BaseAgent


class TravelManagerAgent(BaseAgent):
    """
    Coordinates travel planning for a traveller session.
    Responsible for decomposing a travel request into sub-tasks
    and returning a structured itinerary plan.
    """

    name = "travel_manager"
    description = "Plans and manages end-to-end travel itineraries."

    async def run(self, input_data: dict[str, Any]) -> AgentResult:
        destination = input_data.get("destination")
        dates = input_data.get("dates")
        preferences = input_data.get("preferences", {})

        if not destination:
            return self._err("destination is required")

        plan = self._build_plan(destination, dates, preferences)
        return self._ok(plan)

    def _build_plan(
        self,
        destination: str,
        dates: dict | None,
        preferences: dict,
    ) -> dict:
        return {
            "destination": destination,
            "dates": dates,
            "preferences": preferences,
            "tasks": [
                {"type": "flights", "status": "pending"},
                {"type": "accommodation", "status": "pending"},
                {"type": "itinerary", "status": "pending"},
            ],
            "agent": self.name,
            "session_id": self.context.session_id,
        }
