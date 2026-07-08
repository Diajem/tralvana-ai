"""
GoalReasoner — evaluates goal completeness and planning readiness.

Sprint 1: deterministic scoring from Goal fields. No external APIs.
Sprint 3+: LLM-assisted gap analysis and agent recommendation.
"""

from __future__ import annotations

from typing import Any

_REQUIRED_FIELDS = [
    ("title", 0.15, "Title not set"),
    (
        "goal_type_ne_gen",
        0.10,
        "Goal type is still 'General Travel' — be more specific",
    ),
    ("budget", 0.20, "Budget range (min/max) not specified"),
    ("timeframe", 0.20, "Travel dates or timeframe not provided"),
    ("travellers", 0.10, "Number of travellers not confirmed"),
    ("interests", 0.10, "No travel interests specified"),
    ("success_criteria", 0.10, "Success criteria not defined"),
    ("constraints", 0.05, "No constraints listed (optional but helpful)"),
]

_AGENT_MAP: dict[str, list[str]] = {
    "RELAXATION": ["FlightAgent", "HotelAgent", "ExperienceAgent"],
    "ADVENTURE": ["FlightAgent", "HotelAgent", "ExperienceAgent", "VisaAgent"],
    "FOOTBALL_TRAVEL": ["FlightAgent", "HotelAgent", "ExperienceAgent"],
    "FAMILY_TRIP": ["FlightAgent", "HotelAgent", "ExperienceAgent"],
    "BUSINESS_TRAVEL": ["FlightAgent", "HotelAgent"],
    "FOOD_TOUR": ["FlightAgent", "HotelAgent", "ExperienceAgent"],
    "PHOTOGRAPHY": ["FlightAgent", "HotelAgent", "ExperienceAgent"],
    "PILGRIMAGE": ["FlightAgent", "HotelAgent", "VisaAgent", "ExperienceAgent"],
    "DIASPORA_TRAVEL": ["FlightAgent", "HotelAgent", "VisaAgent", "ExperienceAgent"],
    "ROMANTIC_TRIP": ["FlightAgent", "HotelAgent", "ExperienceAgent"],
    "GENERAL_TRAVEL": ["FlightAgent", "HotelAgent"],
}

_NEXT_ACTIONS: dict[str, list[str]] = {
    "DRAFT": [
        "Specify your budget range",
        "Choose travel dates or a flexible timeframe",
        "Add travel interests to get better recommendations",
        "Describe what success looks like for this trip",
    ],
    "ACTIVE": [
        "Review goal details and confirm they are correct",
        "Confirm number of travellers",
        "Add any travel constraints (e.g. visa restrictions, accessibility needs)",
    ],
    "READY_FOR_PLANNING": [
        "Start searching for flights",
        "Browse hotel options matching your budget",
        "Explore experiences at your destination",
    ],
    "PLANNED": [
        "Review your trip plan",
        "Check visa and documentation requirements",
        "Set up travel insurance",
    ],
    "ARCHIVED": [
        "Create a new goal to restart planning",
    ],
}


class GoalReasoner:
    """
    Returns structured analysis of a Goal's planning readiness.

    Input: goal dict (from GoalService.get()).
    Output: GoalReasoningResult dict with 5 keys.
    """

    def reason(self, goal: dict[str, Any]) -> dict[str, Any]:
        score, missing = self._score(goal)
        status = goal.get("status", "DRAFT")
        goal_type = goal.get("goal_type", "GENERAL_TRAVEL")

        summary = self._summary(goal, score)
        next_actions = _NEXT_ACTIONS.get(status, _NEXT_ACTIONS["DRAFT"])
        agents = _AGENT_MAP.get(goal_type, _AGENT_MAP["GENERAL_TRAVEL"])

        return {
            "goal_summary": summary,
            "missing_information": missing,
            "planning_readiness_score": round(score, 2),
            "recommended_next_actions": next_actions,
            "suitable_agents": agents,
        }

    # ------------------------------------------------------------------

    def _score(self, goal: dict[str, Any]) -> tuple[float, list[str]]:
        score = 0.0
        missing: list[str] = []

        b = goal.get("budget", {})
        t = goal.get("timeframe", {})

        checks = [
            bool(goal.get("title")),
            goal.get("goal_type") not in (None, "GENERAL_TRAVEL"),
            bool(b.get("min_usd") and b.get("max_usd")),
            bool(t.get("earliest") and t.get("latest")),
            goal.get("travellers", {}).get("adults", 0) >= 1,
            bool(goal.get("interests")),
            bool(goal.get("success_criteria")),
            bool(goal.get("constraints")),
        ]

        for i, (_, weight, msg) in enumerate(_REQUIRED_FIELDS):
            if checks[i]:
                score += weight
            else:
                missing.append(msg)

        return score, missing

    def _summary(self, goal: dict[str, Any], score: float) -> str:
        title = goal.get("title", "Untitled goal")
        goal_type = goal.get("goal_type", "GENERAL_TRAVEL").replace("_", " ").title()
        status = goal.get("status", "DRAFT")
        readiness = (
            "ready for planning" if score >= 0.85 else f"{int(score * 100)}% complete"
        )

        b = goal.get("budget", {})
        t = goal.get("timeframe", {})

        parts = [f"**{title}** — {goal_type} | Status: {status} | {readiness}."]

        if b.get("min_usd") and b.get("max_usd"):
            parts.append(
                f"Budget: ${b['min_usd']:,}–${b['max_usd']:,} {b.get('currency', 'USD')}."
            )
        if t.get("earliest") or t.get("duration_days"):
            timeframe_txt = []
            if t.get("earliest"):
                timeframe_txt.append(f"from {t['earliest']}")
            if t.get("latest"):
                timeframe_txt.append(f"to {t['latest']}")
            if t.get("duration_days"):
                timeframe_txt.append(f"{t['duration_days']} days")
            parts.append(f"Timeframe: {', '.join(timeframe_txt)}.")
        if goal.get("interests"):
            parts.append(f"Interests: {', '.join(goal['interests'])}.")

        return " ".join(parts)


goal_reasoner = GoalReasoner()
