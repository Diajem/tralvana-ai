
from ai.concierge.decision_engine import Decision
from ai.concierge.intent_classifier import Intent
from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus


class ResponseComposer:
    """
    Assembles a single coherent traveller-facing answer from specialist agent outputs.

    The traveller should feel they are speaking to an experienced travel consultant,
    not a system reading back a list of data fields.

    Sprint 1: template-driven composition.
    Sprint 3+: LLM-generated narrative with traveller voice matching.
    """

    _PREAMBLES: dict[Intent, str] = {
        Intent.PLAN_TRIP: "Here's what I've put together for your trip.",
        Intent.FLIGHT_SEARCH: "Here are your ranked flight options.",
        Intent.ACCOMMODATION_SEARCH: "Here are your ranked accommodation options.",
        Intent.MODIFY_TRIP: "I can help you make changes to that trip.",
        Intent.VIEW_PROFILE: "Here's what I have on file for you.",
        Intent.UPDATE_PREFERENCES: "I'll update your travel preferences right away.",
        Intent.DESTINATION_QUESTION: "Here's what I know about that destination.",
        Intent.TRAVEL_ADVICE: "Here's my travel advice.",
        Intent.BUDGET_ADVICE: "Here's my budget overview.",
        Intent.GENERAL_CONVERSATION: (
            "I'm Tralvana, your AI travel concierge. "
            "I can help you plan trips, explore destinations, review budgets, and more."
        ),
    }

    def compose(
        self,
        intent: Intent,
        decision: Decision,
        results: list[AgentResult],
        traveller_name: str | None = None,
    ) -> str:
        if not decision.has_enough_information:
            return self._compose_clarification(decision.follow_up_questions)

        if decision.is_safety_sensitive:
            prefix = (
                "⚠️ Please note that this destination currently has active travel advisories. "
                "Check your government's official travel advice before proceeding.\n\n"
            )
        else:
            prefix = ""

        name_prefix = f"{traveller_name}, " if traveller_name else ""
        preamble = self._PREAMBLES.get(intent, "I'm here to help.")
        parts: list[str] = [f"{prefix}{name_prefix}{preamble}"]

        for result in results:
            section = self._section_for(result)
            if section:
                parts.append(section)

        if not results:
            parts.append(
                "I'll bring in live data for flights, hotels, and pricing in a future sprint. "
                "For now, I can give you cost estimates and destination insights."
            )

        if decision.requires_live_data:
            parts.append(
                "_Live pricing and availability will be connected in Sprint 4._"
            )

        return "\n\n".join(parts)

    def compose_greeting(self, traveller_name: str | None = None) -> str:
        name_part = f", {traveller_name}" if traveller_name else ""
        return (
            f"Hello{name_part}! I'm Tralvana, your AI travel concierge. "
            "I can help you plan trips, explore destinations, review budgets, and check visa requirements. "
            "Where would you like to go?"
        )

    def _compose_clarification(self, questions: list[str]) -> str:
        if not questions:
            return "Could you give me a bit more information so I can help you better?"
        intro = "To get started, I need a few details:"
        items = "\n".join(f"- {q}" for q in questions)
        return f"{intro}\n{items}"

    def _section_for(self, result: AgentResult) -> str:
        if result.status == AgentStatus.FAILED:
            return ""

        d = result.data

        if result.agent_name == "budget_agent":
            flight = d.get("estimated_flight_cost", "TBD")
            hotel = d.get("estimated_hotel_per_night", "TBD")
            daily = d.get("estimated_daily_total", "TBD")
            cabin = d.get("cabin_class", "economy")
            return (
                f"**Budget estimate ({cabin} class):** "
                f"Flights from ~{flight}, hotels from ~{hotel}/night, "
                f"daily spend ~{daily}."
            )

        if result.agent_name == "flight_intelligence":
            top = d.get("top_option", {})
            if not top:
                return "**Flights:** No flight options could be generated for this route."
            return (
                f"**Flights:** {d.get('count', 0)} option(s) ranked for "
                f"{d.get('origin', 'origin')} → {d.get('destination', 'destination')}. "
                f"Best match: {top.get('airline')} {top.get('flight_number')} "
                f"({top.get('cabin_class')}, {top.get('stops')} stop"
                f"{'s' if top.get('stops') != 1 else ''}) at {top.get('currency')} "
                f"{top.get('estimated_price')} — match score {top.get('match_score')}. "
                f"{top.get('reasoning', '')}"
            )

        if result.agent_name == "accommodation_intelligence":
            top = d.get("top_option", {})
            if not top:
                return "**Accommodation:** No accommodation options could be generated for this destination."
            return (
                f"**Accommodation:** {d.get('count', 0)} option(s) ranked for "
                f"{d.get('destination', 'destination')}. "
                f"Best match: {top.get('property_name')} "
                f"({top.get('accommodation_type', '').replace('_', ' ').title()}, "
                f"{top.get('star_rating')}-star) at {top.get('currency')} "
                f"{top.get('nightly_price')}/night — match score {top.get('match_score')}. "
                f"{top.get('reasoning', '')}"
            )

        if result.agent_name == "flight_agent":
            dest = d.get("destination", "your destination")
            origin = d.get("origin", "your home airport")
            dates = d.get("date_hint", "dates TBD")
            cabin = d.get("cabin_class", "economy")
            return (
                f"**Flights:** {origin} → {dest} ({dates}), {cabin} class. "
                f"Live pricing available in Sprint 4."
            )

        if result.agent_name == "hotel_agent":
            dest = d.get("destination", "your destination")
            acc_type = d.get("accommodation_type", "hotel")
            prefs = d.get("hotel_preferences", [])
            pref_note = f" with {', '.join(prefs)}" if prefs else ""
            return (
                f"**Accommodation:** {acc_type.title()}{pref_note} in {dest}. "
                f"Live availability in Sprint 4."
            )

        if result.agent_name == "experience_agent":
            dest = d.get("destination", "your destination")
            highlights = d.get("highlights", [])
            tips = d.get("local_tips", [])
            lines = [f"**{dest}:** {', '.join(highlights[:3])}."]
            if tips:
                lines.append(f"_Tip: {tips[0]}_")
            return " ".join(lines)

        if result.agent_name == "visa_agent":
            if result.status == AgentStatus.PARTIAL:
                return (
                    "**Visa:** I couldn't check requirements without your passport country. "
                    "Add it to your profile or check the destination embassy's website."
                )
            dest = d.get("destination", "your destination")
            country = d.get("passport_country", "your country")
            return (
                f"**Visa:** Requirements for {country} nationals visiting {dest} "
                f"will be confirmed via live data in Sprint 5."
            )

        return ""
