from __future__ import annotations

from typing import Any

# Dimension weights — must sum to 1.0. Kept explicit so scoring stays explainable:
# every dimension's contribution can be read straight off SCORE_WEIGHTS.
SCORE_WEIGHTS: dict[str, float] = {
    "interest_fit": 0.30,
    "safety_fit": 0.15,
    "budget_fit": 0.15,
    "transport_fit": 0.10,
    "season_fit": 0.10,
    "family_fit": 0.10,
    "photography_fit": 0.10,
}

# Maps a free-text traveller interest to the objective score field it
# corresponds to. Interests without a direct mapping (e.g. "romance",
# "adventure") contribute a neutral 0.6 rather than being ignored.
INTEREST_SCORE_FIELD: dict[str, str] = {
    "food": "food_score",
    "culture": "culture_score",
    "history": "culture_score",
    "art": "culture_score",
    "football": "football_score",
    "sport": "football_score",
    "nightlife": "nightlife_score",
    "music": "nightlife_score",
    "family": "family_score",
}
_NEUTRAL_INTEREST_SCORE = 0.6


class DestinationScorer:
    """
    Deterministic 0.0-1.0 match scoring for a single normalized destination
    option. Mirrors ai/discovery/flights/flight_scorer.py's and
    ai/discovery/accommodation/accommodation_scorer.py's shape: every
    sub-score is a simple, explainable formula over normalized fields and
    traveller preferences, plus a DNA/goal-type adjustment layer.
    """

    def score(
        self,
        destination: dict[str, Any],
        preferences: dict[str, Any],
        dna: dict[str, Any] | None = None,
        goal_type: str | None = None,
    ) -> dict[str, Any]:
        photography_fit = self._photography_fit(destination)

        breakdown = {
            "interest_fit": self._interest_fit(destination, preferences),
            "safety_fit": destination["safety_score"],
            "budget_fit": self._budget_fit(destination, preferences),
            "transport_fit": destination["transport_access_score"],
            "season_fit": destination["season_score"],
            "family_fit": self._family_fit(destination, preferences),
            "photography_fit": photography_fit,
        }

        base_score = sum(breakdown[k] * SCORE_WEIGHTS[k] for k in SCORE_WEIGHTS)
        adjustment, dna_notes = self._dna_and_goal_adjustment(destination, dna, goal_type)
        match_score = round(min(max(base_score + adjustment, 0.0), 1.0), 2)

        persona_scores = self._persona_scores(destination, breakdown, photography_fit)

        return {
            "match_score": match_score,
            "breakdown": breakdown,
            "adjustment": round(adjustment, 2),
            "dna_notes": dna_notes,
            "persona_scores": persona_scores,
        }

    # ------------------------------------------------------------------

    def _interest_fit(self, d: dict[str, Any], prefs: dict[str, Any]) -> float:
        interests = prefs.get("interests", [])
        if not interests:
            return _NEUTRAL_INTEREST_SCORE
        scores = [
            d[INTEREST_SCORE_FIELD[i.lower()]] if i.lower() in INTEREST_SCORE_FIELD else _NEUTRAL_INTEREST_SCORE
            for i in interests
        ]
        return round(sum(scores) / len(scores), 2)

    def _budget_fit(self, d: dict[str, Any], prefs: dict[str, Any]) -> float:
        budget_style = prefs.get("budget_style", "balanced")
        if budget_style in ("backpacker", "budget"):
            return d["budget_score"]
        if budget_style == "balanced":
            return round(0.5 + 0.5 * d["budget_score"], 2)
        return 0.7

    def _family_fit(self, d: dict[str, Any], prefs: dict[str, Any]) -> float:
        if prefs.get("has_children"):
            return d["family_score"]
        return 0.6

    def _photography_fit(self, d: dict[str, Any]) -> float:
        if "photography" in d.get("_tags", []):
            return 1.0
        return round(min(1.0, d["culture_score"] * 0.6 + d["_popularity"] / 10 * 0.4), 2)

    def _dna_and_goal_adjustment(
        self,
        d: dict[str, Any],
        dna: dict[str, Any] | None,
        goal_type: str | None,
    ) -> tuple[float, list[str]]:
        adjustment = 0.0
        notes: list[str] = []

        traits = (dna or {}).get("traits", {})

        if traits.get("photography_tendency", 0) > 0.5 and "photography" in d.get("_tags", []):
            adjustment += 0.06
            notes.append("Photography-oriented traveller — a photogenic spot boosted.")

        if traits.get("food_focus", 0) > 0.5 and d["food_score"] > 0.6:
            adjustment += 0.06
            notes.append("Food-focused traveller — a strong food scene boosted.")

        if traits.get("sport_focus", 0) > 0.5 and d["football_score"] > 0.6:
            adjustment += 0.08
            notes.append("Sport-focused traveller — football relevance boosted.")

        if traits.get("cultural_curiosity", 0) > 0.5 and d["culture_score"] > 0.6:
            adjustment += 0.05
            notes.append("Culturally curious traveller — cultural relevance boosted.")

        if traits.get("family_orientation", 0) > 0.5 and d["family_score"] > 0.6:
            adjustment += 0.05
            notes.append("Family-oriented traveller — family suitability boosted.")

        if traits.get("budget_consciousness", 0) > 0.5 and d["budget_score"] > 0.6:
            adjustment += 0.05
            notes.append("Budget-conscious traveller — affordability boosted.")

        if goal_type == "FOOTBALL_TRAVEL" and d["football_score"] > 0.6:
            adjustment += 0.08
            notes.append("Football travel goal — football relevance boosted.")

        if goal_type == "FOOD_TOUR" and d["food_score"] > 0.6:
            adjustment += 0.06
            notes.append("Food tour goal — food relevance boosted.")

        if goal_type == "FAMILY_TRIP" and d["family_score"] > 0.6:
            adjustment += 0.06
            notes.append("Family trip goal — family suitability boosted.")

        if goal_type in ("DIASPORA_TRAVEL", "PILGRIMAGE") and {"heritage", "culture"} & set(d.get("_tags", [])):
            adjustment += 0.06
            notes.append(f"{goal_type.replace('_', ' ').title()} goal — heritage relevance boosted.")

        return adjustment, notes

    def _persona_scores(
        self, d: dict[str, Any], breakdown: dict[str, float], photography_fit: float
    ) -> dict[str, float]:
        """Independent, persona-weighted scores — used to label options that
        aren't the overall winner but are still the best fit for a segment."""
        food = d["food_score"] * 0.7 + breakdown["interest_fit"] * 0.3
        football = d["football_score"] * 0.7 + breakdown["interest_fit"] * 0.3
        culture = d["culture_score"] * 0.7 + breakdown["interest_fit"] * 0.3
        family = d["family_score"] * 0.6 + breakdown["safety_fit"] * 0.4
        budget = d["budget_score"]
        photography = photography_fit
        hidden_gem = round(1.0 - d["_popularity"] / 10, 2)
        return {
            "food": round(food, 2),
            "football": round(football, 2),
            "culture": round(culture, 2),
            "family": round(family, 2),
            "budget": round(budget, 2),
            "photography": round(photography, 2),
            "hidden_gem": hidden_gem,
        }


destination_scorer = DestinationScorer()
