from __future__ import annotations

from typing import Any


class DestinationReasoner:
    """
    Turns a DestinationScorer breakdown into a human-readable explanation.

    Explainable AI over black-box scores (ENGINEERING_PRINCIPLES.md #Explainable
    AI): every sentence here traces back to a specific field on the
    destination option or a specific weighted dimension from
    DestinationScorer, never a vague "AI thinks".
    """

    def explain(
        self,
        destination: dict[str, Any],
        score_result: dict[str, Any],
        preferences: dict[str, Any],
    ) -> str:
        breakdown = score_result["breakdown"]
        d = destination
        parts: list[str] = []

        type_label = d["destination_type"].replace("_", " ").title()
        location = f"{d['city']}, {d['country']}" if d["destination_type"] != "CITY" else d["country"]
        parts.append(
            f"{d['name']} ({type_label}, {location}) scores {score_result['match_score']}."
        )

        if breakdown["interest_fit"] >= 0.8:
            parts.append("Strongly matches your stated interests.")
        elif breakdown["interest_fit"] <= 0.4:
            parts.append("Only a loose match for your stated interests.")

        if breakdown["safety_fit"] < 0.6:
            parts.append("Below-average safety rating for the area.")

        if breakdown["budget_fit"] >= 0.8:
            parts.append("Fits comfortably within a budget-conscious travel style.")
        elif breakdown["budget_fit"] <= 0.4:
            parts.append("Tends toward the pricier end for this travel style.")

        if breakdown["transport_fit"] >= 0.8:
            parts.append("Easy to reach — well connected by transport.")
        elif breakdown["transport_fit"] <= 0.4:
            parts.append(f"{d['distance_from_centre']} km out — factor in extra transport time.")

        if breakdown["season_fit"] >= 0.9:
            parts.append("Travel timing lines up with the best season to visit.")
        elif breakdown["season_fit"] <= 0.5:
            parts.append("Outside the typical peak season for this destination.")

        if d["best_for"]:
            parts.append(f"Best for: {', '.join(d['best_for'][:3])}.")

        parts.extend(score_result.get("dna_notes", []))

        return " ".join(parts)


destination_reasoner = DestinationReasoner()
