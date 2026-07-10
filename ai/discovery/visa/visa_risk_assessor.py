from __future__ import annotations

from typing import Any

_PASSPORT_VALIDITY_RULE_MONTHS = 6.0
_LOW_CONFIDENCE_THRESHOLD = 0.5


class VisaRiskAssessor:
    """
    Deterministic risk flags for a single visa assessment.

    Property-intrinsic only, matching the same pattern as every other
    Discovery module's Risk Assessor — it reads the already-normalized
    assessment (and the confidence score computed by VisaScorer) without
    needing any separate traveller preferences parameter. Detects: passport
    expiry risk, transit visa risk, insufficient validity, missing
    documentation, unknown rule, and low confidence. This is explainable
    travel-planning intelligence, not legal advice — see
    docs/VISA_INTELLIGENCE_ENGINE.md.
    """

    def assess(self, option: dict[str, Any], confidence: float) -> list[str]:
        risks: list[str] = []
        o = option

        # Passport expiry risk
        if o["passport_expiry_date"] is None:
            risks.append(
                "Passport expiry date was not supplied — the common 6-month validity "
                "rule could not be checked."
            )
        elif o["passport_validity_months"] < _PASSPORT_VALIDITY_RULE_MONTHS:
            risks.append(
                f"Passport has only {o['passport_validity_months']} month(s) of validity remaining — "
                "many countries require at least 6 months beyond the date of entry."
            )

        # Insufficient validity — passport or authorisation shorter than the trip itself
        if (
            o["passport_validity_months"] is not None
            and o["passport_validity_months"] * 30.44 < o["intended_length_of_stay"]
        ):
            risks.append("Passport validity is shorter than the intended length of stay.")
        if o["max_stay_days"] and o["intended_length_of_stay"] > o["max_stay_days"]:
            risks.append(
                f"Intended stay of {o['intended_length_of_stay']} days exceeds the "
                f"{o['max_stay_days']}-day allowance for this entry category."
            )

        # Transit visa risk
        flagged_transit = [t["country"] for t in o["transit_status"] if t["requires_action"]]
        if flagged_transit:
            risks.append(
                f"Transiting through {', '.join(flagged_transit)} may require its own visa "
                "or authorisation, separate from the destination requirements."
            )

        # Missing documentation
        if o["travel_purpose"] == "OTHER":
            risks.append(
                "Travel purpose was not specified clearly — required documentation may differ "
                "from this general estimate."
            )

        # Unknown rule
        if o["matched_type"] == "unknown":
            risks.append(
                "No specific rule is available for this passport/destination pair — "
                "verify directly with the destination's embassy or consulate."
            )

        # Low confidence
        if confidence < _LOW_CONFIDENCE_THRESHOLD:
            risks.append(
                "Confidence in this assessment is low — verify with an official government "
                "source before booking travel."
            )

        return risks


visa_risk_assessor = VisaRiskAssessor()
