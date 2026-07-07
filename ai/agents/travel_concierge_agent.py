from typing import Any

from ai.agents.base_agent import AgentContext, AgentResult, BaseAgent


class TravelConciergeAgent(BaseAgent):
    """
    Primary AI entry point for all traveller interactions.

    Receives structured intent + entities from ConversationEngine, applies
    the traveller's profile context, and routes work to specialist agents or
    answers directly.

    Sprint 1: rule-based routing with stub outputs.
    Sprint 3+: LLM-powered intent understanding and response generation.
    """

    name = "travel_concierge"
    description = "Primary entry point for all traveller conversations."

    async def run(self, input_data: dict[str, Any]) -> AgentResult:
        intent = input_data.get("intent", "general_conversation")
        message = input_data.get("message", "")
        entities = input_data.get("entities", {})

        handlers = {
            "plan_trip": self._handle_plan_trip,
            "modify_trip": self._handle_modify_trip,
            "view_profile": self._handle_view_profile,
            "update_preferences": self._handle_update_preferences,
            "ask_destination": self._handle_destination_query,
            "travel_advice": self._handle_travel_advice,
            "budget_advice": self._handle_budget_advice,
            "general_conversation": self._handle_general,
        }
        handler = handlers.get(intent, self._handle_general)
        return await handler(message, entities)

    async def _handle_plan_trip(self, message: str, entities: dict) -> AgentResult:
        destination = entities.get("destination")
        if not destination:
            return self._ok({
                "action": "clarify",
                "questions": [
                    "Where would you like to go?",
                    "When are you planning to travel?",
                ],
            })

        profile_applied = self.context.traveller_profile is not None
        return self._ok({
            "action": "plan",
            "destination": destination,
            "date_hint": entities.get("date_hint"),
            "traveller_profile_applied": profile_applied,
            "tasks": [
                {"type": "flights", "status": "pending"},
                {"type": "accommodation", "status": "pending"},
                {"type": "itinerary", "status": "pending"},
            ],
        })

    async def _handle_modify_trip(self, message: str, entities: dict) -> AgentResult:
        return self._ok({
            "action": "clarify",
            "questions": [
                "Which trip would you like to modify?",
                "What change do you need?",
            ],
        })

    async def _handle_view_profile(self, message: str, entities: dict) -> AgentResult:
        if self.context.traveller_profile:
            summary = (
                self.context.traveller_profile
                .get("intelligence", {})
                .get("preference_summary", {})
            )
            return self._ok({"action": "view_profile", "profile_summary": summary})
        return self._ok({"action": "view_profile", "profile_summary": None})

    async def _handle_update_preferences(self, message: str, entities: dict) -> AgentResult:
        return self._ok({
            "action": "update_preferences",
            "note": "Provide your profile ID to update preferences.",
        })

    async def _handle_destination_query(self, message: str, entities: dict) -> AgentResult:
        destination = entities.get("destination", "the destination")
        return self._ok({
            "action": "destination_info",
            "destination": destination,
            "data": "pending",
        })

    async def _handle_travel_advice(self, message: str, entities: dict) -> AgentResult:
        return self._ok({"action": "travel_advice", "advice": "pending"})

    async def _handle_budget_advice(self, message: str, entities: dict) -> AgentResult:
        return self._ok({"action": "budget_advice", "estimate": "pending"})

    async def _handle_general(self, message: str, entities: dict) -> AgentResult:
        return self._ok({
            "action": "greet",
            "response": "How can I help you plan your next trip?",
        })
