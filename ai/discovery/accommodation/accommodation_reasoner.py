from __future__ import annotations

from typing import Any


class AccommodationReasoner:
    """
    Turns an AccommodationScorer breakdown into a human-readable explanation.

    Explainable AI over black-box scores (ENGINEERING_PRINCIPLES.md #Explainable
    AI): every sentence here traces back to a specific field on the property or
    a specific weighted dimension from AccommodationScorer, never a vague "AI thinks".
    """

    def explain(
        self,
        accommodation: dict[str, Any],
        score_result: dict[str, Any],
        preferences: dict[str, Any],
    ) -> str:
        breakdown = score_result["breakdown"]
        a = accommodation
        parts: list[str] = []

        parts.append(
            f"{a['property_name']} ({a['accommodation_type'].replace('_', ' ').title()}, "
            f"{a['star_rating']}-star, {a['neighbourhood']}) scores {score_result['match_score']}."
        )

        if breakdown["price_fit"] >= 0.8:
            parts.append(f"Priced well within budget at {a['currency']} {a['nightly_price']}/night.")
        elif breakdown["price_fit"] <= 0.4:
            parts.append(f"Priced above the comfortable range at {a['currency']} {a['nightly_price']}/night.")

        if breakdown["location_fit"] >= 0.8:
            parts.append(f"Excellent location — {a['distance_to_centre']} km from the centre.")
        elif breakdown["location_fit"] <= 0.4:
            parts.append(f"Further out — {a['distance_to_centre']} km from the centre.")

        if breakdown["breakfast_fit"] < 0.5:
            parts.append("Breakfast is not included.")

        if a["cancellation_policy"] == "non_refundable":
            parts.append("Non-refundable booking policy.")
        elif a["cancellation_policy"] == "free_cancellation":
            parts.append("Free cancellation available.")

        if breakdown["accessibility_fit"] <= 0.2:
            parts.append("No accessibility features listed.")

        if a["review_score"] >= 8.5:
            parts.append(f"Strongly rated by guests ({a['review_score']}/10).")
        elif a["review_score"] < 7.0:
            parts.append(f"Below-average guest rating ({a['review_score']}/10).")

        parts.extend(score_result.get("dna_notes", []))

        return " ".join(parts)


accommodation_reasoner = AccommodationReasoner()
