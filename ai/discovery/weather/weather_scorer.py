from __future__ import annotations

from typing import Any

# Dimension weights — must sum to 1.0, same explainability convention as
# every other Discovery module's SCORE_WEIGHTS. This is weather_suitability_
# score's composition: how comfortable and safe the destination is for THIS
# traveller in THIS month, not just a raw comfort average. See ADR-016.
SCORE_WEIGHTS: dict[str, float] = {
    "temp_fit": 0.30,
    "rainfall_fit": 0.25,
    "humidity_fit": 0.15,
    "hazard_fit": 0.20,
    "daylight_fit": 0.10,
}

_SUITABILITY_LABEL: list[tuple[float, str]] = [
    (0.85, "an excellent match for your travel style"),
    (0.65, "a good match for your travel style"),
    (0.45, "an acceptable match, with some trade-offs"),
    (0.25, "a challenging match — significant trade-offs apply"),
    (0.0, "not a recommended match for this trip"),
]


class WeatherScorer:
    """
    Deterministic 0.0-1.0 weather_suitability_score for a single normalized
    month/destination assessment, plus assessment confidence. Mirrors the
    other Discovery modules' scorer shape (weighted, explainable dimensions
    summing to 1.0, plus a DNA/goal-type adjustment layer) — weighted here
    over the comfort/hazard dimensions the Normalizer already computed.
    """

    def score(
        self,
        option: dict[str, Any],
        dna: dict[str, Any] | None = None,
        goal_type: str | None = None,
    ) -> dict[str, Any]:
        breakdown = {
            "temp_fit": option["_temp_comfort"],
            "rainfall_fit": option["_rainfall_comfort"],
            "humidity_fit": option["_humidity_comfort"],
            "hazard_fit": round(1 - option["_hazard_penalty"], 2),
            "daylight_fit": round(min((option["daylight_hours"] or 10.0) / 16.0, 1.0), 2),
        }

        base_score = sum(breakdown[k] * SCORE_WEIGHTS[k] for k in SCORE_WEIGHTS)
        adjustment, dna_notes = self._dna_and_goal_adjustment(option, dna, goal_type)
        weather_suitability_score = round(min(max(base_score + adjustment, 0.0), 1.0), 2)

        confidence = self._confidence(option)
        personal_suitability = self._personal_suitability(weather_suitability_score, dna_notes)

        return {
            "weather_suitability_score": weather_suitability_score,
            "breakdown": breakdown,
            "adjustment": round(adjustment, 2),
            "dna_notes": dna_notes,
            "confidence": confidence,
            "personal_suitability": personal_suitability,
        }

    # ------------------------------------------------------------------

    def _dna_and_goal_adjustment(
        self,
        option: dict[str, Any],
        dna: dict[str, Any] | None,
        goal_type: str | None,
    ) -> tuple[float, list[str]]:
        adjustment = 0.0
        notes: list[str] = []

        traits = (dna or {}).get("traits", {})
        has_hazards = len(option["hazards"]) > 0

        if traits.get("adventure_seeking", 0) > 0.5 and has_hazards:
            adjustment += 0.05
            notes.append("Adventure-seeking traveller — less deterred by seasonal hazards.")

        if traits.get("photography_tendency", 0) > 0.5 and option["photography_score"] > 0.6:
            adjustment += 0.05
            notes.append("Photography-oriented traveller — strong light and clarity boosted.")

        if traits.get("family_orientation", 0) > 0.5 and option["family_score"] > 0.6:
            adjustment += 0.05
            notes.append("Family-oriented traveller — comfortable, low-hazard conditions boosted.")

        if goal_type == "FAMILY_TRIP" and option["family_score"] > 0.6:
            adjustment += 0.06
            notes.append("Family trip goal — family-friendly conditions boosted.")

        if goal_type == "PHOTOGRAPHY" and option["photography_score"] > 0.6:
            adjustment += 0.06
            notes.append("Photography goal — favourable light conditions boosted.")

        if goal_type == "ADVENTURE" and has_hazards:
            adjustment += 0.04
            notes.append("Adventure travel goal — less deterred by seasonal hazards.")

        return adjustment, notes

    def _confidence(self, option: dict[str, Any]) -> float:
        if not option["matched"]:
            return 0.3
        return 0.9

    def _personal_suitability(self, score: float, dna_notes: list[str]) -> str:
        label = next(text for threshold, text in _SUITABILITY_LABEL if score >= threshold)
        sentence = f"This is {label}."
        if dna_notes:
            sentence += f" {dna_notes[0]}"
        return sentence


weather_scorer = WeatherScorer()
