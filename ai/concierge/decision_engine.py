from dataclasses import dataclass, field
from typing import Any

from ai.concierge.intent_classifier import Intent


# Which specialist agents handle each intent.
_AGENT_MAP: dict[Intent, list[str]] = {
    Intent.PLAN_TRIP: ["flight_agent", "hotel_agent", "budget_agent", "experience_agent", "visa_agent"],
    # FLIGHT_SEARCH and ACCOMMODATION_SEARCH are handled directly by their
    # Discovery Layer engines (ai/discovery/flights/, ai/discovery/accommodation/),
    # not dispatched through the specialist-agent registry — see ConversationEngine.
    Intent.FLIGHT_SEARCH: [],
    Intent.ACCOMMODATION_SEARCH: [],
    Intent.DESTINATION_DISCOVERY: [],
    Intent.BUDGET_ANALYSIS: [],
    Intent.MODIFY_TRIP: ["flight_agent", "hotel_agent"],
    Intent.DESTINATION_QUESTION: ["experience_agent"],
    Intent.TRAVEL_ADVICE: ["experience_agent"],
    Intent.BUDGET_ADVICE: ["budget_agent"],
    Intent.VIEW_PROFILE: [],
    Intent.UPDATE_PREFERENCES: [],
    Intent.GENERAL_CONVERSATION: [],
}

# Simple safety-sensitive destination set.
# Sprint 5: replaced by a live travel advisory API.
_SAFETY_SENSITIVE = {
    "kabul", "mogadishu", "tripoli", "damascus", "khartoum",
}


@dataclass
class Decision:
    has_enough_information: bool
    requires_agents: list[str]
    follow_up_questions: list[str]
    is_safety_sensitive: bool
    requires_live_data: bool
    reasoning: str
    assumptions: list[str] = field(default_factory=list)


class DecisionEngine:
    """
    Decides what agents are needed and whether sufficient context exists
    to proceed, before any agent is invoked.

    Decisions made:
    - Whether enough information exists to proceed.
    - Which specialist agents are required.
    - Whether to ask follow-up questions.
    - Whether the request is safety-sensitive.
    - Whether live data will be needed.

    Sprint 1: deterministic rule-based logic.
    Sprint 3+: LLM-backed reasoning with confidence scoring.
    """

    def decide(
        self,
        intent: Intent,
        entities: dict[str, str],
        profile: dict[str, Any] | None,
    ) -> Decision:
        questions: list[str] = []
        assumptions: list[str] = []

        destination = entities.get("destination", "").lower()

        # --- information completeness ---
        if intent == Intent.PLAN_TRIP:
            if not destination:
                questions.append("Where would you like to go?")
            if not entities.get("date_hint"):
                questions.append("When are you planning to travel?")

        if intent == Intent.FLIGHT_SEARCH:
            if not destination:
                questions.append("Where would you like to fly to?")
            # No date_hint requirement — Flight Intelligence defaults the
            # departure date and records it as an assumption when omitted.

        if intent == Intent.ACCOMMODATION_SEARCH:
            if not destination:
                questions.append("Which destination would you like accommodation for?")
            # No date_hint requirement — Accommodation Intelligence defaults
            # the check-in date and records it as an assumption when omitted.

        has_enough = len(questions) == 0
        agents = _AGENT_MAP.get(intent, []) if has_enough else []

        # --- assumptions ---
        if "visa_agent" in agents:
            if not profile or not profile.get("identity", {}).get("nationality"):
                assumptions.append(
                    "Visa requirements will be checked — add your passport country to profile for accuracy."
                )

        if "budget_agent" in agents:
            if not profile:
                assumptions.append(
                    "Budget estimates use mid-range defaults — no traveller profile found."
                )
            else:
                budget_style = profile.get("preferences", {}).get("budget_style", "balanced")
                assumptions.append(f"Budget estimates based on your '{budget_style}' style.")

        if not profile and intent == Intent.PLAN_TRIP:
            assumptions.append(
                "No profile linked — personalisation is not applied to this request."
            )

        # --- safety check ---
        is_safety = destination in _SAFETY_SENSITIVE

        # --- live data requirement ---
        needs_live = intent in (
            Intent.PLAN_TRIP, Intent.MODIFY_TRIP, Intent.FLIGHT_SEARCH,
            Intent.ACCOMMODATION_SEARCH, Intent.DESTINATION_DISCOVERY, Intent.BUDGET_ANALYSIS,
        )

        return Decision(
            has_enough_information=has_enough,
            requires_agents=agents,
            follow_up_questions=questions,
            is_safety_sensitive=is_safety,
            requires_live_data=needs_live,
            reasoning=self._reasoning(intent, has_enough, questions),
            assumptions=assumptions,
        )

    def _reasoning(self, intent: Intent, has_enough: bool, questions: list[str]) -> str:
        if not has_enough:
            missing = len(questions)
            return (
                f"Cannot proceed with {intent.value}: "
                f"{missing} required input{'s' if missing > 1 else ''} missing."
            )
        agents = _AGENT_MAP.get(intent, [])
        if agents:
            return f"Proceeding with {intent.value} — dispatching {len(agents)} agent(s)."
        return f"Handling {intent.value} directly — no specialist agents needed."
