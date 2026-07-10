from __future__ import annotations

from typing import Any


class WeatherReasoner:
    """
    Turns a WeatherScorer breakdown into a human-readable explanation, plus
    packing advice. This is a travel decision engine, not a forecast —
    every sentence here traces back to a specific field on the assessment
    or a specific weighted dimension from WeatherScorer, never a vague "AI
    thinks". See docs/WEATHER_INTELLIGENCE_ENGINE.md.
    """

    def explain(
        self,
        option: dict[str, Any],
        score_result: dict[str, Any],
        alternative_months: list[dict[str, Any]],
    ) -> str:
        o = option
        parts: list[str] = []

        parts.append(
            f"{o['destination'].title()} in {o['month_name']} ({o['season'].replace('_', ' ').title()}) "
            f"scores {score_result['weather_suitability_score']} for this trip."
        )

        if o["average_temperature"] is not None:
            parts.append(f"Average temperature is around {o['average_temperature']}°C.")

        breakdown = score_result["breakdown"]
        if breakdown["rainfall_fit"] <= 0.4:
            parts.append(f"{o['rainfall_level'].replace('_', ' ').title()} rainfall is a significant trade-off this month.")
        elif breakdown["rainfall_fit"] >= 0.9:
            parts.append("Rainfall is minimal this month.")

        if breakdown["hazard_fit"] < 0.7 and o["hazards"]:
            hazard_labels = ", ".join(h.replace("_", " ") for h in o["hazards"])
            parts.append(f"This month falls within {hazard_labels} for this destination.")

        if breakdown["temp_fit"] >= 0.8:
            parts.append("Outdoor suitability is strong — comfortable temperatures for sightseeing and activities.")
        elif breakdown["temp_fit"] <= 0.4:
            parts.append("Outdoor suitability is limited by temperature extremes this month.")

        if o["photography_score"] >= 0.7:
            parts.append("Good light and clarity for photography this month.")
        elif o["photography_score"] <= 0.4:
            parts.append("Photography conditions are below average — expect haze, cloud cover, or short daylight.")

        if o["family_score"] >= 0.7:
            parts.append("Well suited to travelling with children.")
        elif o["family_score"] <= 0.4:
            parts.append("Less ideal for travelling with children this month.")

        parts.append(score_result["personal_suitability"])

        if alternative_months:
            best = alternative_months[0]
            parts.append(
                f"{best['month_name']} scores higher ({best['weather_suitability_score']}) if your "
                "dates are flexible."
            )

        if not o["matched"]:
            parts.append(
                "No specific climate data is available for this destination — this is a general estimate only."
            )

        return " ".join(parts)

    def packing_advice(self, option: dict[str, Any]) -> list[str]:
        o = option
        advice: list[str] = []

        if o["rainfall_level"] in ("HIGH", "VERY_HIGH"):
            advice.append("Waterproof jacket and footwear")
        if o["average_temperature"] is not None and o["average_temperature"] >= 30:
            advice.append("Lightweight clothing and sun protection")
        if o["average_temperature"] is not None and o["average_temperature"] <= 5:
            advice.append("Warm layers and insulated outerwear")
        if o["humidity_level"] in ("HIGH", "VERY_HIGH"):
            advice.append("Breathable fabrics for high humidity")
        if "flood" in o["hazards"] or o["rainfall_level"] == "VERY_HIGH":
            advice.append("Insect repellent — wet-season conditions favour mosquitoes")
        if o["daylight_hours"] is not None and o["daylight_hours"] < 9:
            advice.append("A torch/flashlight — limited daylight hours")
        if any(h in o["hazards"] for h in ("hurricane", "typhoon")):
            advice.append("Travel insurance with severe-weather cover")

        if not advice:
            advice.append("Standard travel clothing — no significant weather extremes this month")

        return advice


weather_reasoner = WeatherReasoner()
