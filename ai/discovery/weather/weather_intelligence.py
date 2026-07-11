from __future__ import annotations

from typing import Any

from ai.discovery.weather.mock_weather_provider import MockWeatherProvider
from ai.discovery.weather.weather_normalizer import weather_normalizer
from ai.discovery.weather.weather_reasoner import weather_reasoner
from ai.discovery.weather.weather_risk_assessor import weather_risk_assessor
from ai.discovery.weather.weather_scorer import weather_scorer

_STATUS_THRESHOLDS: list[tuple[float, str]] = [
    (0.85, "EXCELLENT"), (0.65, "GOOD"), (0.45, "ACCEPTABLE"), (0.25, "CHALLENGING"),
]
_DEFAULT_STATUS = "NOT_RECOMMENDED"

_RECOMMENDATION: dict[str, str] = {
    "EXCELLENT": "Great time to visit — no significant weather or safety concerns.",
    "GOOD": "A good time to visit — minor trade-offs, nothing that should change your plans.",
    "ACCEPTABLE": "A workable time to visit — go in with clear expectations about the trade-offs.",
    "CHALLENGING": "Consider a different month if your dates are flexible — this period has real trade-offs.",
    "NOT_RECOMMENDED": "Consider a different month — this period has significant weather or safety concerns.",
}

# Only surface a better month as an "alternative" if it clears this margin
# over the primary month — avoids noisy, marginal suggestions.
_ALTERNATIVE_MARGIN = 0.05
_MAX_ALTERNATIVES = 2


class WeatherIntelligence:
    """
    Orchestrates a single weather/safety assessment: resolve the climate
    record -> normalize -> score -> explain -> assess risk -> recommend.
    Mirrors the role of every other Discovery module's top-level
    orchestrator for its domain. See docs/DISCOVERY_LAYER_PATTERN.md.

    Sixth and final Discovery Layer module (T-020), alongside Flight
    (T-015), Accommodation (T-016), Destination (T-017), Budget (T-018),
    and Visa (T-019) Intelligence. Like Visa Intelligence, this produces one
    assessment rather than a ranked list — but unlike Visa, the request
    itself is dual-mode: a specific month assesses that month; an omitted
    month finds the best month across the year and assesses that one
    instead, the same "give a useful answer either way" idea Destination
    Intelligence established for city vs. no-city (ADR-013). See ADR-016.

    Deliberately independent — no import from ai/discovery/destinations/ or
    ai/discovery/budget/. Destination and duration are passed in as plain
    values, not resolved from another Discovery module's output, so this
    module can be consumed standalone by a future Trip Brain without a
    dependency edge back into Discovery Layer internals.

    This is a travel decision engine, not a forecast. Sprint 1:
    MockWeatherProvider only. Sprint 4+: real climate data feed behind the
    same month()/year() interface; only the Normalizer changes.
    """

    def __init__(self, provider: MockWeatherProvider | None = None) -> None:
        self._provider = provider or MockWeatherProvider()

    def analyse(
        self,
        destination: str,
        month_of_travel: int | None = None,
        profile: dict[str, Any] | None = None,
        goal: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        assumptions: list[str] = []
        year = self._provider.year(destination)

        dna: dict[str, Any] | None = None
        if profile:
            try:
                from ai.intelligence import dna_inference_service
                dna = dna_inference_service.infer(profile).to_dict()
            except Exception:
                dna = None
        else:
            assumptions.append("No traveller profile linked — scoring uses default preferences only.")

        goal_type = (goal or {}).get("goal_type")

        year_scored = [self._score_month_from_raw(m, dna, goal_type) for m in year] if year else []

        if month_of_travel is None:
            if year_scored:
                best = max(year_scored, key=lambda s: s["score_result"]["weather_suitability_score"])
                month_of_travel = best["option"]["month_of_travel"]
                assumptions.append(f"No travel month specified — showing the best month to visit ({best['option']['month_name']}).")
            else:
                month_of_travel = 6
                assumptions.append(
                    "No travel month specified and the destination is not in the mock climate "
                    "catalogue — defaulting to June for a general estimate."
                )

        raw = self._provider.month(destination, month_of_travel)
        if not raw["matched"]:
            assumptions.append(
                f"'{destination}' is not in the mock climate catalogue "
                f"({', '.join(self._provider.known_destinations())}) — a general estimate was used."
            )

        primary = self._score_month_from_raw(raw, dna, goal_type)
        option, score_result = primary["option"], primary["score_result"]

        alternative_months = self._alternative_months(year_scored, month_of_travel)

        explanation = weather_reasoner.explain(option, score_result, alternative_months)
        packing_recommendations = weather_reasoner.packing_advice(option)
        risk_result = weather_risk_assessor.assess(option)

        weather_status = self._status(score_result["weather_suitability_score"])
        recommendation = _RECOMMENDATION[weather_status]
        if alternative_months and weather_status not in ("EXCELLENT", "GOOD"):
            recommendation += f" {alternative_months[0]['month_name']} is a stronger option if your dates are flexible."

        assumptions.append(
            "Weather and safety data are deterministic mock climate profiles — no live forecast "
            "or advisory service was queried. This is a travel decision aid, not a forecast."
        )

        return {
            "destination": option["destination"],
            "month_of_travel": option["month_of_travel"],
            "season": option["season"],
            "average_temperature": option["average_temperature"],
            "rainfall_level": option["rainfall_level"],
            "humidity_level": option["humidity_level"],
            "daylight_hours": option["daylight_hours"],
            "weather_summary": self._weather_summary(option),
            "weather_suitability_score": score_result["weather_suitability_score"],
            "outdoor_activity_score": option["outdoor_activity_score"],
            "photography_score": option["photography_score"],
            "family_score": option["family_score"],
            "transport_disruption_risk": risk_result["transport_disruption_risk"],
            "natural_hazard_risk": risk_result["natural_hazard_risk"],
            "health_risk": risk_result["health_risk"],
            "personal_suitability": score_result["personal_suitability"],
            "packing_recommendations": packing_recommendations,
            "safety_summary": risk_result["safety_summary"],
            "risks": risk_result["risks"],
            "assumptions": assumptions,
            "confidence": score_result["confidence"],
            "weather_status": weather_status,
            "recommendation": recommendation,
            "explanation": explanation,
            "alternative_months": alternative_months,
        }

    # ------------------------------------------------------------------

    def _score_month_from_raw(
        self, raw: dict[str, Any], dna: dict[str, Any] | None, goal_type: str | None
    ) -> dict[str, Any]:
        option = weather_normalizer.normalize(raw)
        score_result = weather_scorer.score(option, dna=dna, goal_type=goal_type)
        return {"option": option, "score_result": score_result}

    def _alternative_months(
        self, year_scored: list[dict[str, Any]], primary_month: int
    ) -> list[dict[str, Any]]:
        if not year_scored:
            return []
        primary_score = next(
            (s["score_result"]["weather_suitability_score"] for s in year_scored
             if s["option"]["month_of_travel"] == primary_month),
            0.0,
        )
        better = [
            s for s in year_scored
            if s["option"]["month_of_travel"] != primary_month
            and s["score_result"]["weather_suitability_score"] >= primary_score + _ALTERNATIVE_MARGIN
        ]
        better.sort(key=lambda s: s["score_result"]["weather_suitability_score"], reverse=True)
        return [
            {
                "month": s["option"]["month_of_travel"],
                "month_name": s["option"]["month_name"],
                "weather_status": self._status(s["score_result"]["weather_suitability_score"]),
                "weather_suitability_score": s["score_result"]["weather_suitability_score"],
            }
            for s in better[:_MAX_ALTERNATIVES]
        ]

    def _status(self, score: float) -> str:
        for threshold, status in _STATUS_THRESHOLDS:
            if score >= threshold:
                return status
        return _DEFAULT_STATUS

    def _weather_summary(self, option: dict[str, Any]) -> str:
        if not option["matched"]:
            return f"No climate data available for {option['destination']} in {option['month_name']}."
        return (
            f"{option['season'].replace('_', ' ').title()}, around {option['average_temperature']}°C, "
            f"{option['rainfall_level'].replace('_', ' ').lower()} rainfall, "
            f"{option['humidity_level'].replace('_', ' ').lower()} humidity."
        )


# Routed through the Intelligence Gateway (T-025) — see the matching
# comment in ai/discovery/flights/flight_intelligence.py for why this
# import is placed here rather than at the top of the file.
from travelos.intelligence_gateway.discovery_adapters import GatewayWeatherProvider  # noqa: E402

weather_intelligence = WeatherIntelligence(provider=GatewayWeatherProvider())
