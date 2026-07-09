from __future__ import annotations

from typing import Any

_FAR_TRANSIT_KM = 1.0
_FAR_CENTRE_KM = 5.0
_LOW_REVIEW_SCORE = 6.0
_LOW_SAFETY_SCORE = 0.5


class AccommodationRiskAssessor:
    """
    Deterministic risk flags for a single normalized accommodation option.

    Property-intrinsic only — no preferences parameter, matching
    ai/discovery/flights/flight_risk_assessor.py's pattern. Sprint 1:
    rule-based over the normalized fields. Sprint 4+: incorporate live
    review-fraud and safety-incident data per AccommodationProvider once
    one is wired in.
    """

    def assess(self, accommodation: dict[str, Any]) -> list[str]:
        risks: list[str] = []
        a = accommodation

        if a["distance_to_transport"] > _FAR_TRANSIT_KM:
            risks.append(
                f"{a['distance_to_transport']} km from public transport — may require taxis or a long walk."
            )

        if a["distance_to_centre"] > _FAR_CENTRE_KM:
            risks.append(
                f"{a['distance_to_centre']} km from the city centre — factor in extra transport time and cost."
            )

        if a["cancellation_policy"] == "non_refundable":
            risks.append("Non-refundable booking — cancellation forfeits the full cost.")

        if a["review_score"] < _LOW_REVIEW_SCORE:
            risks.append(f"Below-average guest reviews ({a['review_score']}/10).")

        if a["safety_score"] < _LOW_SAFETY_SCORE:
            risks.append("Below-average safety rating for this area.")

        if not a["breakfast_included"] and a["distance_to_centre"] > _FAR_CENTRE_KM:
            risks.append("No breakfast included and far from the centre — plan meal logistics in advance.")

        if not a["accessibility_features"]:
            risks.append("No accessibility features listed — confirm directly if step-free access is required.")

        return risks


accommodation_risk_assessor = AccommodationRiskAssessor()
