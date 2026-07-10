from __future__ import annotations

from typing import Any

_RAINFALL_COMFORT: dict[str, float] = {"LOW": 1.0, "MODERATE": 0.7, "HIGH": 0.4, "VERY_HIGH": 0.15, "UNKNOWN": 0.5}
_HUMIDITY_COMFORT: dict[str, float] = {"LOW": 1.0, "MODERATE": 0.75, "HIGH": 0.45, "VERY_HIGH": 0.2, "UNKNOWN": 0.5}
_IDEAL_TEMP_C = 21.0

_MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


class WeatherNormalizer:
    """
    Converts a raw MockWeatherProvider month record into the canonical
    internal schema, and computes the objective (preference-independent)
    scores every downstream stage relies on: outdoor_activity_score,
    photography_score, family_score. These are properties of the month/
    destination combination itself, not of any one traveller. See
    docs/DISCOVERY_LAYER_PATTERN.md.

    weather_suitability_score is deliberately NOT computed here — unlike
    the objective scores above, it is this module's subjective, weighted
    composite (this module's equivalent of match_score) and is computed by
    WeatherScorer instead. See ADR-016.
    """

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        temp_comfort = self._temp_comfort(raw["avg_temp_c"])
        rainfall_comfort = _RAINFALL_COMFORT.get(raw["rainfall"], 0.5)
        humidity_comfort = _HUMIDITY_COMFORT.get(raw["humidity"], 0.5)
        hazard_penalty = min(len(raw["hazards"]) * 0.2, 0.6)
        daylight_fraction = min((raw["daylight_hours"] or 10.0) / 16.0, 1.0)

        return {
            "destination": raw["destination"],
            "month_of_travel": raw["month_of_travel"],
            "month_name": _MONTH_NAMES[raw["month_of_travel"]],
            "matched": raw["matched"],
            "season": raw["season"],
            "average_temperature": raw["avg_temp_c"],
            "rainfall_level": raw["rainfall"],
            "humidity_level": raw["humidity"],
            "daylight_hours": raw["daylight_hours"],
            "hazards": raw["hazards"],
            "_temp_comfort": temp_comfort,
            "_rainfall_comfort": rainfall_comfort,
            "_humidity_comfort": humidity_comfort,
            "_hazard_penalty": hazard_penalty,
            "outdoor_activity_score": round(
                max(0.0, min(1.0, 0.4 * rainfall_comfort + 0.3 * temp_comfort
                              + 0.2 * daylight_fraction + 0.1 * (1 - hazard_penalty))), 2
            ),
            "photography_score": round(
                max(0.0, min(1.0, 0.5 * rainfall_comfort + 0.3 * daylight_fraction
                              + 0.2 * humidity_comfort)), 2
            ),
            "family_score": round(
                max(0.0, min(1.0, 0.4 * temp_comfort + 0.3 * (1 - hazard_penalty)
                              + 0.3 * rainfall_comfort)), 2
            ),
        }

    # ------------------------------------------------------------------

    def _temp_comfort(self, avg_temp_c: float | None) -> float:
        if avg_temp_c is None:
            return 0.5
        distance = abs(avg_temp_c - _IDEAL_TEMP_C)
        return round(max(0.0, 1.0 - distance / 25.0), 2)


weather_normalizer = WeatherNormalizer()
