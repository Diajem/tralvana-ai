from __future__ import annotations

from typing import Any

# Fallback tables when destination is not in the knowledge graph
_DAILY_USD: dict[str, int] = {
    "backpacker": 40,
    "budget": 65,
    "balanced": 150,
    "comfort": 300,
    "luxury": 650,
}

_FLIGHT_USD: dict[str, int] = {
    "economy": 650,
    "business": 2200,
    "first": 5000,
}

_ACCOMMODATION_SHARE = 0.45
_FOOD_SHARE = 0.25
_ACTIVITIES_SHARE = 0.20
_MISC_SHARE = 0.10


class BudgetEstimator:
    """
    Estimates trip cost using BudgetReasoner when the destination is in the
    knowledge graph, or falls back to static global averages.

    Sprint 3+: integrate live flight/hotel pricing APIs.
    """

    def estimate(
        self,
        destination: str,
        duration_days: int,
        budget_style: str,
        cabin_class: str,
        adults: int = 1,
        profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        mock_profile = {
            "preferences": {"budget_style": budget_style, "cabin_class": cabin_class}
        }

        # Try knowledge graph first
        try:
            from ai.intelligence.reasoning.budget_reasoner import budget_reasoner

            result = budget_reasoner.reason(destination, duration_days, mock_profile)
            if result.success:
                return self._from_reasoner(
                    result.data, adults, duration_days, budget_style, cabin_class
                )
        except Exception:
            pass

        # Fallback
        return self._from_static(
            destination, duration_days, budget_style, cabin_class, adults
        )

    # ------------------------------------------------------------------

    def _from_reasoner(
        self,
        data: dict[str, Any],
        adults: int,
        duration_days: int,
        budget_style: str,
        cabin_class: str,
    ) -> dict[str, Any]:
        bd = data["daily_breakdown_usd"]
        flight_pp = data["flight_estimate_usd"]

        accommodation = bd["accommodation"] * duration_days * adults
        food = bd["food"] * duration_days * adults
        activities = bd["activities"] * duration_days * adults
        misc = bd["miscellaneous"] * duration_days * adults
        flights = flight_pp * adults
        total = data["total_estimate_usd"] * adults

        return {
            "flights_usd": flights,
            "accommodation_usd": accommodation,
            "food_usd": food,
            "activities_usd": activities,
            "miscellaneous_usd": misc,
            "total_estimate_usd": total,
            "per_person_usd": data["total_estimate_usd"],
            "total_range_usd": {
                "low": round(total * 0.85),
                "high": round(total * 1.20),
            },
            "basis": f"{budget_style} style, {duration_days} days, {cabin_class} class, {adults} adult(s)",
            "source": "knowledge_graph",
            "notes": [
                "Estimates in USD — convert before booking",
                "No live pricing used",
                "Does not include travel insurance",
            ],
        }

    def _from_static(
        self,
        destination: str,
        duration_days: int,
        budget_style: str,
        cabin_class: str,
        adults: int,
    ) -> dict[str, Any]:
        daily_pp = _DAILY_USD.get(budget_style, _DAILY_USD["balanced"])
        flight_pp = _FLIGHT_USD.get(cabin_class, _FLIGHT_USD["economy"])

        accommodation = round(daily_pp * _ACCOMMODATION_SHARE * duration_days * adults)
        food = round(daily_pp * _FOOD_SHARE * duration_days * adults)
        activities = round(daily_pp * _ACTIVITIES_SHARE * duration_days * adults)
        misc = round(daily_pp * _MISC_SHARE * duration_days * adults)
        flights = flight_pp * adults
        total = flights + (daily_pp * duration_days * adults)

        return {
            "flights_usd": flights,
            "accommodation_usd": accommodation,
            "food_usd": food,
            "activities_usd": activities,
            "miscellaneous_usd": misc,
            "total_estimate_usd": round(total),
            "per_person_usd": round(total / max(adults, 1)),
            "total_range_usd": {
                "low": round(total * 0.85),
                "high": round(total * 1.20),
            },
            "basis": f"{budget_style} style, {duration_days} days, {cabin_class} class, {adults} adult(s)",
            "source": "static_fallback",
            "notes": [
                "Destination not found in knowledge graph — global average rates used",
                "Estimates in USD — convert before booking",
                "Does not include travel insurance",
            ],
        }


budget_estimator = BudgetEstimator()
