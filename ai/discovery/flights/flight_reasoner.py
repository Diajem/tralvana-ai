from __future__ import annotations

from typing import Any


class FlightReasoner:
    """
    Turns a FlightScorer breakdown into a human-readable explanation.

    Explainable AI over black-box scores (ENGINEERING_PRINCIPLES.md #Explainable
    AI): every sentence here traces back to a specific field on the flight or
    a specific weighted dimension from FlightScorer, never a vague "AI thinks".
    """

    def explain(
        self,
        flight: dict[str, Any],
        score_result: dict[str, Any],
        preferences: dict[str, Any],
    ) -> str:
        breakdown = score_result["breakdown"]
        parts: list[str] = []

        parts.append(
            f"{flight['airline']} {flight['flight_number']} "
            f"({flight['stops']} stop{'s' if flight['stops'] != 1 else ''}, "
            f"{flight['total_duration']}) scores {score_result['match_score']} "
            f"for a {preferences.get('cabin_class', 'economy')} traveller."
        )

        if breakdown["price_fit"] >= 0.8:
            parts.append(f"Priced well within budget at {flight['currency']} {flight['estimated_price']}.")
        elif breakdown["price_fit"] <= 0.4:
            parts.append(f"Priced above the comfortable range at {flight['currency']} {flight['estimated_price']}.")

        if breakdown["layover_tolerance"] >= 0.85 and flight["stops"] == 0:
            parts.append("Direct flight — no layover risk.")
        elif flight["stops"] >= 1:
            parts.append(f"Includes a {flight['layover_duration']} layover.")

        if breakdown["baggage_fit"] < 0.5:
            parts.append("Checked baggage is not included — may need to be added separately.")

        if breakdown["time_of_day_fit"] <= 0.3:
            parts.append(f"Departs at {flight['departure_time']} — a red-eye departure.")

        if flight["refundability"] == "non_refundable":
            parts.append("Fare is non-refundable.")
        if flight["flexibility"] == "flexible":
            parts.append("Date changes are permitted without a rebooking fee.")

        parts.extend(score_result.get("dna_notes", []))

        return " ".join(parts)


flight_reasoner = FlightReasoner()
