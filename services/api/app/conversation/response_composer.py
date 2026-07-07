from typing import Any


class ResponseComposer:
    """
    Assembles natural-language replies from agent outputs and session state.
    Sprint 1: template-based. Sprint 3+: LLM-generated narrative.
    """

    _PREAMBLES: dict[str, str] = {
        "plan_trip": "I'll help you plan that trip.",
        "modify_trip": "I can help you make changes to your trip.",
        "view_profile": "Here's what I have on file for you.",
        "update_preferences": "I'll update your travel preferences.",
        "ask_destination": "Let me share what I know about that destination.",
        "travel_advice": "Here's my travel advice.",
        "budget_advice": "Let me help with the budget.",
        "general_conversation": "I'm Tralvana, your AI travel concierge. How can I help you today?",
    }

    def compose(
        self,
        intent: str,
        agent_output: Any,
        traveller_name: str | None = None,
        pending_questions: list[str] | None = None,
    ) -> str:
        prefix = f"{traveller_name}, " if traveller_name else ""
        preamble = self._PREAMBLES.get(intent, "I'm here to help.")
        parts: list[str] = [f"{prefix}{preamble}"]

        if agent_output:
            parts.append(self._format_output(intent, agent_output))

        if pending_questions:
            parts.append("To continue, I need a few more details:")
            for q in pending_questions:
                parts.append(f"- {q}")

        return " ".join(parts)

    def compose_greeting(self, traveller_name: str | None = None) -> str:
        name_part = f", {traveller_name}" if traveller_name else ""
        return (
            f"Hello{name_part}! I'm Tralvana, your AI travel concierge. "
            "Where would you like to go?"
        )

    def compose_clarification(self, questions: list[str]) -> str:
        if not questions:
            return "Could you tell me a bit more?"
        intro = "I need a bit more information:"
        items = "\n".join(f"- {q}" for q in questions)
        return f"{intro}\n{items}"

    def compose_error(self, message: str) -> str:
        return (
            f"I'm sorry, something went wrong: {message}. "
            "Please try again in a moment."
        )

    def _format_output(self, intent: str, output: Any) -> str:
        if not isinstance(output, dict):
            return str(output)

        if intent == "plan_trip":
            destination = output.get("destination", "your destination")
            tasks = output.get("tasks", [])
            task_names = ", ".join(t.get("type", "") for t in tasks if t.get("type"))
            if task_names:
                return f"I'm arranging {task_names} for {destination}."
            return f"I'm putting together your trip to {destination}."

        if intent == "view_profile":
            summary = output.get("profile_summary")
            if summary:
                name = summary.get("name", "")
                style = summary.get("budget_style", "")
                cabin = summary.get("cabin_class", "")
                return f"Profile: {name} — {style} traveller, {cabin} cabin."

        return ""
