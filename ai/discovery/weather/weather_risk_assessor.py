from __future__ import annotations

from typing import Any

_EXTREME_HEAT_C = 32.0
_EXTREME_COLD_C = 0.0
_HEAT_STRESS_C = 28.0


class WeatherRiskAssessor:
    """
    Deterministic risk assessment for a single normalized month/destination
    option. Property-intrinsic only, matching every other Discovery
    module's Risk Assessor — no preferences parameter. Assesses: heavy
    rain, extreme heat, extreme cold, typhoon season, hurricane season,
    flood risk, wildfire season, transport disruption, and health
    considerations.

    Unlike the other five Discovery modules' Risk Assessors (which return
    a flat list[str]), this one returns a richer structure — the itemized
    `risks` list plus three categorical risk-level fields
    (transport_disruption_risk, natural_hazard_risk, health_risk) and a
    one-line safety_summary — because the Weather Assessment model requires
    those as distinct fields, not just itemized messages. See ADR-016.
    """

    def assess(self, option: dict[str, Any]) -> dict[str, Any]:
        o = option
        risks: list[str] = []
        hazards = set(o["hazards"])

        # Heavy rain
        if o["rainfall_level"] in ("HIGH", "VERY_HIGH"):
            risks.append(f"{o['rainfall_level'].replace('_', ' ').title()} rainfall expected — plan indoor alternatives.")

        # Extreme heat
        if "extreme_heat" in hazards or (o["average_temperature"] or 0) >= _EXTREME_HEAT_C:
            risks.append("Extreme heat risk — limit midday outdoor exposure and stay hydrated.")

        # Extreme cold
        if "extreme_cold" in hazards or (o["average_temperature"] is not None and o["average_temperature"] <= _EXTREME_COLD_C):
            risks.append("Extreme cold risk — pack insulated clothing and check for weather-related delays.")

        # Typhoon season
        if "typhoon" in hazards:
            risks.append("Typhoon season — monitor forecasts and flight/ferry status closely.")

        # Hurricane season
        if "hurricane" in hazards:
            risks.append("Hurricane season — monitor advisories and consider travel insurance with storm cover.")

        # Flood risk
        if "flood" in hazards:
            risks.append("Elevated flood risk this month — some routes or attractions may be affected.")

        # Wildfire season
        if "wildfire" in hazards:
            risks.append("Wildfire season — air quality and access to some natural areas may be affected.")

        # Transport disruption
        disruptive = hazards & {"flood", "typhoon", "hurricane"}
        transport_disruption_risk = self._transport_disruption_risk(o, disruptive)
        if transport_disruption_risk in ("HIGH", "SEVERE"):
            risks.append("Transport disruption is likely this month — build buffer time into connections.")

        # Health considerations
        health_risk = self._health_risk(o, hazards)
        if health_risk in ("HIGH", "SEVERE"):
            if "flood" in hazards or o["rainfall_level"] == "VERY_HIGH":
                risks.append("Wet-season conditions increase mosquito-borne illness risk — consider repellent and prophylaxis advice.")
            else:
                risks.append("High heat and humidity combination raises heat-stress risk — pace outdoor activity accordingly.")

        # Unknown destination
        if not o["matched"]:
            risks.append("No specific climate data available for this destination — treat this as a general estimate only.")

        natural_hazard_risk = self._natural_hazard_risk(hazards)

        return {
            "risks": risks,
            "transport_disruption_risk": transport_disruption_risk,
            "natural_hazard_risk": natural_hazard_risk,
            "health_risk": health_risk,
            "safety_summary": self._safety_summary(natural_hazard_risk, transport_disruption_risk, health_risk),
        }

    # ------------------------------------------------------------------

    def _transport_disruption_risk(self, option: dict[str, Any], disruptive_hazards: set[str]) -> str:
        if disruptive_hazards or option["rainfall_level"] == "VERY_HIGH":
            return "HIGH"
        if option["rainfall_level"] == "HIGH":
            return "MODERATE"
        return "LOW"

    def _natural_hazard_risk(self, hazards: set[str]) -> str:
        if hazards & {"typhoon", "hurricane"}:
            return "SEVERE"
        if hazards & {"flood", "wildfire"}:
            return "HIGH"
        if hazards & {"extreme_heat", "extreme_cold"}:
            return "MODERATE"
        return "LOW"

    def _health_risk(self, option: dict[str, Any], hazards: set[str]) -> str:
        temp = option["average_temperature"] or 0
        if option["humidity_level"] == "VERY_HIGH" and temp >= _HEAT_STRESS_C:
            return "HIGH"
        if "flood" in hazards and option["rainfall_level"] in ("HIGH", "VERY_HIGH"):
            return "HIGH"
        if option["humidity_level"] == "HIGH" and temp >= _HEAT_STRESS_C:
            return "MODERATE"
        return "LOW"

    def _safety_summary(self, natural_hazard_risk: str, transport_disruption_risk: str, health_risk: str) -> str:
        levels = {natural_hazard_risk, transport_disruption_risk, health_risk}
        if "SEVERE" in levels or levels == {"HIGH"}:
            return "Elevated risk period — active seasonal hazards should be monitored closely before travel."
        if "HIGH" in levels:
            return "Some elevated risk factors this month — check advisories before travel."
        if "MODERATE" in levels:
            return "Minor seasonal risk factors — no major concerns."
        return "No significant weather-related safety concerns this month."


weather_risk_assessor = WeatherRiskAssessor()
