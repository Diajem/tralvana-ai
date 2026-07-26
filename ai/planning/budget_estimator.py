from __future__ import annotations

from typing import Any

from ai.discovery.budget.budget_cost_model import raw_budget_candidate
from ai.discovery.budget.budget_normalizer import budget_normalizer


class BudgetEstimator:
    """
    Estimates trip cost using BudgetReasoner when the destination is in the
    knowledge graph, or the canonical Budget Intelligence cost model.

    No live price is claimed. T-033 removes the separate fallback tables that
    previously drifted from Budget Intelligence.
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

        return self._from_cost_model(
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

    def _from_cost_model(
        self,
        destination: str,
        duration_days: int,
        budget_style: str,
        cabin_class: str,
        adults: int,
    ) -> dict[str, Any]:
        option = budget_normalizer.normalize(
            raw_budget_candidate(
                destination=destination,
                budget_style=budget_style,
                cabin_class=cabin_class,
                duration_days=duration_days,
                adults=adults,
                children=0,
            )
        )
        total = option["total_cost_usd"]

        return {
            "flights_usd": option["flight_cost_usd"],
            "accommodation_usd": option["accommodation_usd"],
            "food_usd": option["food_usd"],
            "activities_usd": option["activities_usd"],
            "miscellaneous_usd": option["misc_usd"],
            "total_estimate_usd": total,
            "per_person_usd": round(total / max(adults, 1)),
            "total_range_usd": {
                "low": round(total * 0.85),
                "high": round(total * 1.20),
            },
            "basis": f"{budget_style} style, {duration_days} days, {cabin_class} class, {adults} adult(s)",
            "source": "budget_intelligence_cost_model",
            "notes": [
                (
                    "Estimated regional rates from Budget Intelligence used; "
                    "unknown destinations use its global-average band"
                ),
                "Estimates in USD — convert before booking",
                "No live flight or accommodation pricing used",
                "Does not include travel insurance",
            ],
        }


budget_estimator = BudgetEstimator()
