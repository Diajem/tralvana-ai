from __future__ import annotations

from ai.intelligence.knowledge.relationships import RelationshipType
from ai.intelligence.reasoning.base_reasoner import BaseReasoner, ReasoningResult

_RISK_SUMMARY: dict[str, str] = {
    "low":      "Low risk destination. Standard travel precautions apply.",
    "medium":   "Moderate risk. Be vigilant in crowded areas; keep copies of travel documents.",
    "high":     "High risk. Review your government's travel advisory before booking. Avoid non-essential travel.",
    "critical": "Critical risk. Most governments advise against all travel. Do not proceed without specialist security advice.",
}

_PRECAUTIONS: dict[str, list[str]] = {
    "low":    ["Secure your valuables", "Purchase travel insurance", "Register with your embassy"],
    "medium": ["Stay in tourist areas after dark", "Avoid displaying expensive items", "Keep emergency contacts saved",
               "Purchase travel insurance with medical cover", "Register with your embassy"],
    "high":   ["Monitor travel advisories daily", "Avoid protests and large gatherings",
               "Have an emergency exit plan", "Secure travel insurance with evacuation cover",
               "Register your trip with your government's travel portal"],
    "critical":["Only travel if absolutely essential", "Seek professional security consultancy",
                "Ensure evacuation insurance is in place", "Do not travel alone"],
}

_EMBASSY_HINT = "Contact your country's embassy in {country} before travelling. Most embassies maintain 24-hour emergency lines."


class SafetyReasoner(BaseReasoner):
    """
    Reasons about safety and visa requirements for a destination.

    Sprint 1: uses Country.safety_level + VisaRequirement entities from the graph.
    Sprint 3+: live FCDO/US State Department advisory feeds.
    """

    def reason(
        self,
        destination: str,
        passport_country_iso: str = "NG",
        traveller_profile: dict | None = None,
        **_,
    ) -> ReasoningResult:
        city, country = self._city_and_country(destination)
        if city is None:
            return self._not_found(destination, f"'{destination}' is not in the knowledge graph.")

        safety_level = country.safety_level if country else "unknown"
        visa = self._visa(passport_country_iso, country.iso_code if country else "")
        languages = self._languages(country) if country else []
        health_tips = self._health_tips(country)

        return ReasoningResult(
            reasoner_name="SafetyReasoner",
            subject=destination,
            success=True,
            confidence=0.65,
            data={
                "destination": destination,
                "country": country.name if country else "Unknown",
                "country_iso": country.iso_code if country else "",
                "safety_level": safety_level,
                "risk_summary": _RISK_SUMMARY.get(safety_level, "Safety level unknown."),
                "precautions": _PRECAUTIONS.get(safety_level, _PRECAUTIONS["low"]),
                "embassy_hint": _EMBASSY_HINT.format(country=country.name if country else "destination"),
                "visa": {
                    "requirement": visa.requirement if visa else "Unknown — verify with your embassy",
                    "max_stay_days": visa.max_stay_days if visa else None,
                    "notes": visa.notes if visa else "No visa data in Sprint 1 for this passport/destination pair.",
                } if True else None,
                "local_languages": languages,
                "health_tips": health_tips,
                "data_source": "Sprint 1 static knowledge graph",
                "advisory_note": (
                    "Always check your government's official travel advisory for the most current information "
                    "before booking or travelling."
                ),
            },
            assumptions=[f"Passport country assumed: {passport_country_iso}"],
            limitations=["No live FCDO/State Dept feed; safety levels are static Sprint 1 data"],
        )

    # ------------------------------------------------------------------

    def _visa(self, from_iso: str, to_iso: str):
        visa_reqs = self._ks.load_entities("VisaRequirement")
        return next(
            (v for v in visa_reqs if v.from_country_iso == from_iso and v.to_country_iso == to_iso),
            None,
        )

    def _languages(self, country) -> list[dict]:
        langs = self._ks.get_connected_entities(country.id, "Language", RelationshipType.SPEAKS, "outbound")
        return [{"name": l.name, "iso": l.iso_code, "native": l.native_name} for l in langs]

    def _health_tips(self, country) -> list[str]:
        if country is None:
            return []
        tips = ["Ensure routine vaccinations are up to date."]
        if country.continent == "Africa":
            tips += ["Consult a travel health clinic about malaria prophylaxis.", "Consider yellow fever vaccination (may be required)."]
        if country.safety_level in ("medium", "high", "critical"):
            tips.append("Confirm your travel insurance covers emergency medical evacuation.")
        return tips


safety_reasoner = SafetyReasoner()
