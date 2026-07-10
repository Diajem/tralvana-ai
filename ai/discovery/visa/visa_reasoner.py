from __future__ import annotations

from typing import Any

_STATUS_LABELS: dict[str, str] = {
    "VISA_NOT_REQUIRED": "no visa is required",
    "VISA_REQUIRED": "a visa is required",
    "ETA_REQUIRED": "an Electronic Travel Authorisation (ETA) is required",
    "EVISA_AVAILABLE": "an e-Visa is required (available online)",
    "CHECK_MANUALLY": "requirements could not be determined automatically",
    "ENTRY_RESTRICTED": "entry may be restricted",
}


class VisaReasoner:
    """
    Turns a VisaScorer breakdown into a human-readable explanation. This is
    explainable travel-planning intelligence, not legal advice — every
    sentence here traces back to a specific field on the assessment or a
    specific weighted dimension from VisaScorer, never a vague "AI thinks".
    See docs/VISA_INTELLIGENCE_ENGINE.md.
    """

    def explain(self, option: dict[str, Any], score_result: dict[str, Any]) -> str:
        o = option
        parts: list[str] = []

        status_label = _STATUS_LABELS.get(o["visa_status"], o["visa_status"])
        purpose = o["travel_purpose"].replace("_", " ").lower()
        parts.append(
            f"As a {o['nationality']} passport holder travelling to {o['destination_country'].title()} "
            f"for {purpose}, {status_label}."
        )

        if o["max_stay_days"]:
            parts.append(f"This covers stays of up to {o['max_stay_days']} days.")
            if o["intended_length_of_stay"] > o["max_stay_days"]:
                parts.append(
                    f"Your intended {o['intended_length_of_stay']}-day stay exceeds that allowance — "
                    "a different visa category is likely needed for the full trip."
                )

        if o["passport_validity_months"] is None:
            parts.append("Passport expiry date was not supplied — validity could not be verified.")
        else:
            months = o["passport_validity_months"]
            if months < 6:
                parts.append(
                    f"Only {months} month(s) of passport validity remain — below the 6 months "
                    "many countries require beyond the date of entry."
                )
            else:
                parts.append(f"{months} month(s) of passport validity remain — meets the common 6-month rule.")

        if o["transit_countries"]:
            flagged = [t["country"] for t in o["transit_status"] if t["requires_action"]]
            if flagged:
                parts.append(
                    f"Transiting through {', '.join(flagged)} may require its own visa or authorisation — "
                    "check each transit leg separately."
                )
            else:
                parts.append(
                    f"Transit through {', '.join(o['transit_countries'])} does not appear to need separate action."
                )
        else:
            parts.append("No transit countries specified — this assumes direct routing.")

        if o["matched_type"] == "unknown":
            parts.append(
                "No specific rule is available for this passport/destination pair — "
                "this is a general estimate only."
            )

        parts.append(self._next_step(o["visa_status"], o["processing_time"]))

        return " ".join(parts)

    def _next_step(self, status: str, processing_time: str) -> str:
        if status == "VISA_NOT_REQUIRED":
            return "No visa application is needed for this trip."
        if status == "CHECK_MANUALLY":
            return "Contact the destination's embassy or consulate directly to confirm requirements."
        if status == "ENTRY_RESTRICTED":
            return "Verify current entry restrictions with official government sources before planning travel."
        item = "visa" if status == "VISA_REQUIRED" else "travel authorisation"
        return f"Apply for the required {item} in advance — typical processing time: {processing_time}."


visa_reasoner = VisaReasoner()
