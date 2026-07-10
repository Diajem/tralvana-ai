from __future__ import annotations

from typing import Any

from ai.discovery.visa.mock_visa_provider import MockVisaProvider
from ai.discovery.visa.visa_normalizer import visa_normalizer
from ai.discovery.visa.visa_reasoner import visa_reasoner
from ai.discovery.visa.visa_risk_assessor import visa_risk_assessor
from ai.discovery.visa.visa_scorer import visa_scorer

_RECOMMENDATION: dict[str, str] = {
    "VISA_NOT_REQUIRED": "No visa action needed for this trip.",
    "VISA_REQUIRED": "Apply for a visa before travelling — do not book non-refundable flights until it is approved.",
    "ETA_REQUIRED": "Apply for an Electronic Travel Authorisation (ETA) before departure.",
    "EVISA_AVAILABLE": "Apply for an e-Visa online before departure.",
    "CHECK_MANUALLY": "Contact the destination's embassy or consulate directly — no reliable rule is available.",
    "ENTRY_RESTRICTED": "Entry may be restricted — verify current restrictions with official sources before planning travel.",
}


class VisaIntelligence:
    """
    Orchestrates a single visa assessment: look up the rule -> resolve
    transit-country implications -> normalize -> score confidence -> explain
    -> assess risk -> recommend. Mirrors the role of every other Discovery
    module's top-level orchestrator (ai/discovery/flights/flight_intelligence.py,
    etc.) for its domain. See docs/DISCOVERY_LAYER_PATTERN.md.

    Fifth Discovery Layer module (T-019), alongside Flight (T-015),
    Accommodation (T-016), Destination (T-017), and Budget (T-018)
    Intelligence. Unlike those four, this module assesses one specific
    passport/destination/purpose combination rather than ranking several
    provider-returned options — there is nothing to rank, so there is no
    labelling algorithm here; the single "recommendation" field takes its
    place. See ADR-015 for why.

    This is explainable travel-planning intelligence, not legal advice.
    Sprint 1: MockVisaProvider only, deterministic rule tables. Sprint 4+:
    real immigration data feed behind the same lookup() interface; only the
    Normalizer changes.
    """

    def __init__(self, provider: MockVisaProvider | None = None) -> None:
        self._provider = provider or MockVisaProvider()

    def check(
        self,
        passport_country: str,
        destination_country: str,
        nationality: str | None = None,
        transit_countries: list[str] | None = None,
        travel_purpose: str = "TOURISM",
        intended_length_of_stay: int = 14,
        passport_expiry_date: str | None = None,
    ) -> dict[str, Any]:
        assumptions: list[str] = []
        transit_countries = transit_countries or []

        raw = self._provider.lookup(passport_country, destination_country, travel_purpose)
        nationality = nationality or raw["passport_country"]
        if raw["matched_type"] == "unknown":
            assumptions.append(
                f"'{passport_country}' or '{destination_country}' is not in the mock rule set "
                f"(known nationalities: {', '.join(self._provider.known_nationalities())}; "
                f"known destinations: {', '.join(self._provider.known_destinations())}) — "
                "a general fallback was used."
            )

        transit_status = self._resolve_transit(passport_country, transit_countries)
        if not passport_expiry_date:
            assumptions.append("No passport expiry date supplied — validity could not be verified.")

        option = visa_normalizer.normalize(
            raw,
            nationality=nationality,
            transit_countries=transit_countries,
            transit_status=transit_status,
            travel_purpose=travel_purpose,
            intended_length_of_stay=intended_length_of_stay,
            passport_expiry_date=passport_expiry_date,
        )

        score_result = visa_scorer.score(option)
        confidence = score_result["confidence"]
        explanation = visa_reasoner.explain(option, score_result)
        risks = visa_risk_assessor.assess(option, confidence)
        recommendation = _RECOMMENDATION.get(option["visa_status"], "Verify requirements manually.")

        assumptions.append(
            "Visa data is a deterministic mock rule set — no live government, embassy, or "
            "Timatic-style data was queried. This is not legal advice."
        )

        return {
            **option,
            "confidence": confidence,
            "risks": risks,
            "assumptions": assumptions,
            "recommendation": recommendation,
            "explanation": explanation,
        }

    # ------------------------------------------------------------------

    def _resolve_transit(self, passport_country: str, transit_countries: list[str]) -> list[dict[str, Any]]:
        resolved: list[dict[str, Any]] = []
        for country in transit_countries:
            rule = self._provider.lookup(passport_country, country)
            resolved.append({
                "country": country,
                "status": rule["status"],
                "requires_action": rule["status"] != "VISA_NOT_REQUIRED",
            })
        return resolved


visa_intelligence = VisaIntelligence()
