from __future__ import annotations

from typing import Any

_COMMON_RISKS = [
    {
        "type": "financial",
        "severity": "low",
        "description": "Exchange rate fluctuations may increase the cost of the trip.",
        "mitigation": "Buy travel money in advance or use a fee-free travel card.",
    },
    {
        "type": "logistics",
        "severity": "low",
        "description": "No live flight or hotel availability has been confirmed.",
        "mitigation": "Check availability and book early — especially in peak season.",
    },
    {
        "type": "health",
        "severity": "low",
        "description": "Health requirements (vaccinations, medication) have not been verified.",
        "mitigation": "Consult a travel clinic at least 6 weeks before departure.",
    },
]

_TROPICAL_RISK = {
    "type": "health",
    "severity": "medium",
    "description": "Tropical destination — malaria prophylaxis and yellow fever vaccination may be required.",
    "mitigation": "Visit a travel health clinic and check NHS Fit For Travel or CDC for the latest advice.",
}

_TROPICAL_KEYWORDS = {"lagos", "accra", "nairobi", "kampala", "dar es salaam", "kinshasa", "abuja"}


class RiskAssessor:
    """
    Produces a list of travel risks for a destination.

    Sources (in priority order):
    1. SafetyReasoner from the Travel Intelligence Layer (knowledge graph).
    2. Static common risks that apply to every trip.
    3. Heuristic tropical-health risk for known African cities.

    Sprint 3+: integrate live FCDO / US State Dept travel advisories.
    """

    def assess(
        self,
        destination: str,
        passport_iso: str = "NG",
        profile: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        risks: list[dict[str, Any]] = []

        # Try knowledge graph safety data
        try:
            from ai.intelligence.reasoning.safety_reasoner import safety_reasoner
            result = safety_reasoner.reason(
                destination, passport_country_iso=passport_iso
            )
            if result.success:
                risks.extend(self._from_safety_result(result.data))
        except Exception:
            pass

        # Tropical health heuristic
        if destination.lower() in _TROPICAL_KEYWORDS:
            risks.append(_TROPICAL_RISK)

        # Always append common risks
        risks.extend(_COMMON_RISKS)

        return risks

    # ------------------------------------------------------------------

    def _from_safety_result(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        extracted: list[dict[str, Any]] = []

        level = data.get("safety_level", "low")
        if level in ("medium", "high"):
            extracted.append({
                "type": "safety",
                "severity": level,
                "description": data.get("risk_summary", f"Safety level rated {level} for this destination."),
                "mitigation": "; ".join(data.get("precautions", [])[:3]) or "Stay vigilant and follow local guidance.",
            })

        visa = data.get("visa", {})
        req = visa.get("requirement", "")
        if req in ("required", "evisa"):
            label = "eVisa" if req == "evisa" else "Visa"
            extracted.append({
                "type": "visa",
                "severity": "medium",
                "description": f"{label} required — not automatically granted at the border.",
                "mitigation": f"Apply via official government portal at least 6-8 weeks before travel. {visa.get('notes', '')}",
            })

        return extracted


risk_assessor = RiskAssessor()
