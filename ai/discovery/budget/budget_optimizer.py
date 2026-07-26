"""Deterministic cross-trip budget allocation over existing tier estimates."""

from __future__ import annotations

from typing import Any

from ai.discovery.budget.budget_cost_model import STYLES
from ai.discovery.budget.budget_normalizer import budget_normalizer
from ai.discovery.budget.mock_budget_provider import MockBudgetProvider

_STYLE_INDEX = {style: index for index, style in enumerate(STYLES)}
_DATA_SOURCE = "ESTIMATED_REGIONAL_RATES"


class BudgetOptimizer:
    """Choose the strongest allowed tier per trip within one USD cap.

    Each trip may move from its preferred tier down to, but never below, its
    declared minimum tier. Priority weights make a downgrade more expensive in
    the optimisation objective for important trips. The engine never upgrades
    above the preferred tier merely to consume spare budget.
    """

    def __init__(self, provider: MockBudgetProvider | None = None) -> None:
        self._provider = provider or MockBudgetProvider()

    def optimise(
        self,
        *,
        portfolio_budget_usd: int,
        trips: list[dict[str, Any]],
    ) -> dict[str, Any]:
        prepared = [self._prepare_trip(trip) for trip in trips]
        preferred_total = sum(
            trip["options"][trip["preferred_style"]]["total_cost_usd"]
            for trip in prepared
        )
        minimum_total = sum(
            trip["options"][trip["minimum_style"]]["total_cost_usd"]
            for trip in prepared
        )

        feasible = minimum_total <= portfolio_budget_usd
        if feasible:
            selected = self._select_within_cap(
                prepared,
                portfolio_budget_usd,
            )
        else:
            selected = [
                trip["options"][trip["minimum_style"]]
                for trip in prepared
            ]

        allocations = [
            self._allocation(trip, option)
            for trip, option in zip(prepared, selected, strict=True)
        ]
        optimised_total = sum(
            allocation["selected_cost_usd"] for allocation in allocations
        )
        savings = preferred_total - optimised_total
        shortfall = max(minimum_total - portfolio_budget_usd, 0)
        remaining = max(portfolio_budget_usd - optimised_total, 0)
        changed_count = sum(allocation["changed"] for allocation in allocations)

        risks = [
            "All costs are deterministic regional estimates, not live quotes.",
            "Exchange rates, taxes, fees, seasonality, and availability can change totals.",
        ]
        if changed_count:
            risks.append(
                "One or more trips were moved below the preferred tier to protect "
                "the portfolio cap."
            )
        if not feasible:
            risks.append(
                "The portfolio cap cannot fund every trip at its declared minimum tier."
            )

        summary = (
            f"Allocated {len(allocations)} trip(s) at an estimated "
            f"${optimised_total:,} against a ${portfolio_budget_usd:,} cap."
        )
        if feasible:
            summary += (
                f" Estimated savings versus every preferred tier: ${savings:,}; "
                f"remaining headroom: ${remaining:,}."
            )
        else:
            summary += (
                f" Even the minimum acceptable tiers exceed the cap by "
                f"${shortfall:,}."
            )

        return {
            "feasible": feasible,
            "portfolio_budget_usd": portfolio_budget_usd,
            "preferred_total_usd": preferred_total,
            "minimum_total_usd": minimum_total,
            "optimised_total_usd": optimised_total,
            "savings_usd": savings,
            "remaining_budget_usd": remaining,
            "shortfall_usd": shortfall,
            "data_source": _DATA_SOURCE,
            "estimate_confidence": self._confidence(selected),
            "allocations": allocations,
            "assumptions": [
                "All trips are estimated in USD using the existing Budget Intelligence regional rates.",
                "A child is estimated at 75% of an adult's flight and daily cost.",
                "Trips may be downgraded only as far as their declared minimum tier.",
                "No trip is upgraded above its preferred tier merely to spend unused budget.",
                "No live flight, accommodation, tax, fee, or exchange-rate data is used.",
            ],
            "risks": risks,
            "next_actions": [
                "Review every changed tier and its comfort trade-off.",
                "Replace estimates with live flight and accommodation quotes before booking.",
                (
                    "Increase the cap, remove a trip, or lower a minimum tier."
                    if not feasible
                    else "Keep a contingency reserve for price movement and travel insurance."
                ),
            ],
            "summary": summary,
        }

    def _prepare_trip(self, trip: dict[str, Any]) -> dict[str, Any]:
        raw_options = self._provider.search(
            trip.get("destination"),
            duration_days=trip["duration_days"],
            adults=trip["adults"],
            children=trip["children"],
        )
        options = {
            raw["budget_style"]: budget_normalizer.normalize(raw)
            for raw in raw_options
        }
        return {**trip, "options": options}

    def _select_within_cap(
        self,
        trips: list[dict[str, Any]],
        cap: int,
    ) -> list[dict[str, Any]]:
        # Pareto frontier: (cost, weighted preference utility, choices).
        states: list[tuple[int, float, list[dict[str, Any]]]] = [
            (0, 0.0, [])
        ]
        for trip in trips:
            minimum = _STYLE_INDEX[trip["minimum_style"]]
            preferred = _STYLE_INDEX[trip["preferred_style"]]
            candidates = [
                trip["options"][style]
                for style in STYLES[minimum : preferred + 1]
            ]
            by_cost: dict[
                int,
                tuple[float, list[dict[str, Any]]],
            ] = {}
            for cost, utility, choices in states:
                for option in candidates:
                    new_cost = cost + option["total_cost_usd"]
                    if new_cost > cap:
                        continue
                    new_utility = utility + self._utility(trip, option)
                    current = by_cost.get(new_cost)
                    if current is None or new_utility > current[0]:
                        by_cost[new_cost] = (
                            new_utility,
                            [*choices, option],
                        )

            states = self._pareto_frontier(by_cost)

        _, _, choices = max(
            states,
            key=lambda state: (state[1], -state[0]),
        )
        return choices

    def _pareto_frontier(
        self,
        by_cost: dict[int, tuple[float, list[dict[str, Any]]]],
    ) -> list[tuple[int, float, list[dict[str, Any]]]]:
        frontier: list[tuple[int, float, list[dict[str, Any]]]] = []
        best_utility = -1.0
        for cost in sorted(by_cost):
            utility, choices = by_cost[cost]
            if utility > best_utility:
                frontier.append((cost, utility, choices))
                best_utility = utility
        return frontier

    def _utility(
        self,
        trip: dict[str, Any],
        option: dict[str, Any],
    ) -> float:
        minimum = _STYLE_INDEX[trip["minimum_style"]]
        preferred = _STYLE_INDEX[trip["preferred_style"]]
        selected = _STYLE_INDEX[option["budget_style"]]
        span = max(preferred - minimum, 1)
        preference_fit = 1.0 - ((preferred - selected) / span)
        priority_weight = 1.0 + ((trip["priority"] - 1) * 0.5)
        return round(preference_fit * priority_weight, 6)

    def _allocation(
        self,
        trip: dict[str, Any],
        selected: dict[str, Any],
    ) -> dict[str, Any]:
        preferred = trip["options"][trip["preferred_style"]]
        changed = selected["budget_style"] != trip["preferred_style"]
        if changed:
            tradeoff = (
                f"Reduced from {trip['preferred_style']} to "
                f"{selected['budget_style']} to protect the shared cap; "
                f"priority {trip['priority']}/5."
            )
        else:
            tradeoff = "Preferred tier retained."

        return {
            "trip_reference": trip["trip_reference"],
            "destination": trip.get("destination"),
            "priority": trip["priority"],
            "preferred_style": trip["preferred_style"],
            "minimum_style": trip["minimum_style"],
            "selected_style": selected["budget_style"],
            "preferred_cost_usd": preferred["total_cost_usd"],
            "selected_cost_usd": selected["total_cost_usd"],
            "savings_usd": (
                preferred["total_cost_usd"] - selected["total_cost_usd"]
            ),
            "changed": changed,
            "tradeoff": tradeoff,
            "cost_breakdown": {
                "flights_usd": selected["flight_cost_usd"],
                "accommodation_usd": selected["accommodation_usd"],
                "food_usd": selected["food_usd"],
                "activities_usd": selected["activities_usd"],
                "miscellaneous_usd": selected["misc_usd"],
            },
            "cost_certainty_score": selected["cost_certainty_score"],
            "data_source": _DATA_SOURCE,
        }

    def _confidence(self, selected: list[dict[str, Any]]) -> float:
        if not selected:
            return 0.0
        average_certainty = sum(
            option["cost_certainty_score"] for option in selected
        ) / len(selected)
        # These remain static estimates even when a tier is relatively stable.
        return round(average_certainty * 0.7, 2)


budget_optimizer = BudgetOptimizer()
