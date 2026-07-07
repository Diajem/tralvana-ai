from typing import Any

from ai.shared.agent_context import AgentContext
from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus

_ESTIMATES: dict[str, dict[str, int]] = {
    "backpacker": {"flight": 400,  "hotel_night": 30,  "daily_total": 60},
    "budget":     {"flight": 600,  "hotel_night": 60,  "daily_total": 100},
    "balanced":   {"flight": 900,  "hotel_night": 120, "daily_total": 180},
    "comfort":    {"flight": 1800, "hotel_night": 250, "daily_total": 350},
    "luxury":     {"flight": 5000, "hotel_night": 600, "daily_total": 800},
}


class BudgetAgent:
    """
    Estimates travel costs based on the traveller's budget style.
    Sprint 1: mock deterministic logic.
    Sprint 4+: live pricing from flight and hotel APIs.
    """

    name = "budget_agent"

    def __init__(self, context: AgentContext) -> None:
        self.context = context

    async def run(self, input_data: dict[str, Any]) -> AgentResult:
        prefs: dict[str, Any] = {}
        if self.context.traveller_profile:
            prefs = self.context.traveller_profile.get("preferences", {})

        budget_style = prefs.get("budget_style", "balanced")
        cabin = prefs.get("cabin_class", "economy")
        currency = prefs.get("preferred_currency", "USD")
        est = _ESTIMATES.get(budget_style, _ESTIMATES["balanced"])

        assumptions = [f"Budget style applied: '{budget_style}'"]
        if not self.context.traveller_profile:
            assumptions.append("No profile linked — mid-range defaults used.")
        if budget_style == "luxury" and cabin != "first":
            assumptions.append("Luxury budget typically pairs with first-class cabin.")

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.SUCCESS,
            confidence=0.7,
            data={
                "budget_style": budget_style,
                "cabin_class": cabin,
                "currency": currency,
                "estimated_flight_cost": f"{est['flight']} {currency}",
                "estimated_hotel_per_night": f"{est['hotel_night']} {currency}",
                "estimated_daily_total": f"{est['daily_total']} {currency}",
            },
            assumptions=assumptions,
            recommendations=[
                f"Book early for {cabin} class at this estimate.",
                "Prices vary by season — confirm closer to travel date.",
                "Consider flexible dates for better flight pricing.",
            ],
            risks=["Fuel surcharges and taxes may add 15–25% to flight costs."],
            next_actions=["confirm_flight_budget", "confirm_hotel_budget"],
        )
