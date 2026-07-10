from __future__ import annotations

from typing import Any


class BudgetOptionReasoner:
    """
    Turns a BudgetScorer breakdown into a human-readable explanation.

    Named BudgetOptionReasoner (not BudgetReasoner) to stay distinct from
    ai.intelligence.reasoning.budget_reasoner.BudgetReasoner — that one
    produces a single-style cost estimate for goal readiness scoring and
    trip planning; this one explains one ranked candidate among several
    styles being compared. See docs/BUDGET_INTELLIGENCE_ENGINE.md.

    Explainable AI over black-box scores (ENGINEERING_PRINCIPLES.md #Explainable
    AI): every sentence here traces back to a specific field on the budget
    option or a specific weighted dimension from BudgetScorer, never a vague
    "AI thinks".
    """

    def explain(
        self,
        option: dict[str, Any],
        score_result: dict[str, Any],
        preferences: dict[str, Any],
    ) -> str:
        breakdown = score_result["breakdown"]
        o = option
        parts: list[str] = []

        style_label = o["budget_style"].title()
        scope = f"in {o['destination']}" if o["destination"] else "for your trip"
        parts.append(
            f"{style_label} tier {scope} totals {o['currency']} {o['total_cost_usd']} "
            f"over {o['duration_days']} day(s) — scores {score_result['match_score']}."
        )

        max_usd = preferences.get("budget_max_usd")
        if max_usd:
            if o["total_cost_usd"] <= max_usd:
                parts.append(f"Fits within your {o['currency']} {max_usd} budget cap.")
            else:
                over = o["total_cost_usd"] - max_usd
                parts.append(f"Exceeds your {o['currency']} {max_usd} budget cap by {o['currency']} {over}.")

        if breakdown["style_fit"] >= 0.8:
            parts.append(f"Closely matches your '{preferences.get('budget_style', 'balanced')}' travel style.")
        elif breakdown["style_fit"] <= 0.3:
            parts.append(f"A significant step away from your usual '{preferences.get('budget_style', 'balanced')}' style.")

        if breakdown["affordability_fit"] >= 0.8:
            parts.append("Strong affordability for a budget-conscious style.")

        if breakdown["family_fit"] >= 0.8:
            parts.append("Well suited to travelling with children.")
        elif preferences.get("has_children") and breakdown["family_fit"] <= 0.4:
            parts.append("Not ideally suited to travelling with children.")

        parts.append(
            f"Breakdown — flights {o['currency']} {o['flight_cost_usd']}, "
            f"accommodation {o['currency']} {o['accommodation_usd']}, "
            f"food {o['currency']} {o['food_usd']}, "
            f"activities {o['currency']} {o['activities_usd']}, "
            f"miscellaneous {o['currency']} {o['misc_usd']}."
        )

        parts.extend(score_result.get("dna_notes", []))

        return " ".join(parts)


budget_option_reasoner = BudgetOptionReasoner()
