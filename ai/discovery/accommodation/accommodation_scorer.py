from __future__ import annotations

from typing import Any

# Dimension weights — must sum to 1.0. Kept explicit so scoring stays explainable:
# every dimension's contribution can be read straight off SCORE_WEIGHTS.
SCORE_WEIGHTS: dict[str, float] = {
    "price_fit": 0.20,
    "type_preference_fit": 0.10,
    "location_fit": 0.15,
    "breakfast_fit": 0.08,
    "cancellation_flexibility_fit": 0.10,
    "accessibility_fit": 0.10,
    "family_fit": 0.07,
    "business_fit": 0.05,
    "review_score_fit": 0.10,
    "safety_score_fit": 0.05,
}

_CANCELLATION_SCORE: dict[str, float] = {
    "free_cancellation": 1.0,
    "partial_refund": 0.6,
    "non_refundable": 0.2,
}


class AccommodationScorer:
    """
    Deterministic 0.0-1.0 match scoring for a single normalized accommodation
    option. Mirrors ai/discovery/flights/flight_scorer.py's shape: every
    sub-score is a simple, explainable formula over normalized fields and
    traveller preferences, plus a DNA/goal-type adjustment layer.
    """

    def score(
        self,
        accommodation: dict[str, Any],
        preferences: dict[str, Any],
        dna: dict[str, Any] | None = None,
        goal_type: str | None = None,
    ) -> dict[str, Any]:
        breakdown = {
            "price_fit": self._price_fit(accommodation, preferences),
            "type_preference_fit": self._type_preference_fit(accommodation, preferences),
            "location_fit": self._location_fit(accommodation, preferences),
            "breakfast_fit": self._breakfast_fit(accommodation, preferences),
            "cancellation_flexibility_fit": self._cancellation_fit(accommodation, preferences),
            "accessibility_fit": self._accessibility_fit(accommodation, preferences),
            "family_fit": self._family_fit(accommodation, preferences),
            "business_fit": self._business_fit(accommodation, preferences),
            "review_score_fit": round(accommodation["review_score"] / 10, 2),
            "safety_score_fit": accommodation["safety_score"],
        }

        base_score = sum(breakdown[k] * SCORE_WEIGHTS[k] for k in SCORE_WEIGHTS)
        adjustment, dna_notes = self._dna_and_goal_adjustment(accommodation, dna, goal_type)
        match_score = round(min(max(base_score + adjustment, 0.0), 1.0), 2)

        persona_scores = self._persona_scores(accommodation, breakdown)

        return {
            "match_score": match_score,
            "breakdown": breakdown,
            "adjustment": round(adjustment, 2),
            "dna_notes": dna_notes,
            "persona_scores": persona_scores,
        }

    # ------------------------------------------------------------------

    def _price_fit(self, a: dict[str, Any], prefs: dict[str, Any]) -> float:
        price = a["nightly_price"]
        ceiling = prefs.get("max_price_usd")
        if not ceiling or ceiling <= 0:
            return 0.6
        ratio = price / ceiling
        if ratio <= 0.7:
            return 1.0
        if ratio <= 1.0:
            return round(1.0 - (ratio - 0.7) * 1.0, 2)
        return round(max(0.0, 0.7 - (ratio - 1.0)), 2)

    def _type_preference_fit(self, a: dict[str, Any], prefs: dict[str, Any]) -> float:
        preferred = prefs.get("accommodation_type")
        if not preferred:
            return 0.7
        return 1.0 if a["accommodation_type"] == preferred else 0.4

    def _location_fit(self, a: dict[str, Any], prefs: dict[str, Any]) -> float:
        if prefs.get("location_preference") == "central":
            return a["location_score"]
        return 0.7

    def _breakfast_fit(self, a: dict[str, Any], prefs: dict[str, Any]) -> float:
        if not prefs.get("needs_breakfast"):
            return 0.8
        return 1.0 if a["breakfast_included"] else 0.3

    def _cancellation_fit(self, a: dict[str, Any], prefs: dict[str, Any]) -> float:
        base = _CANCELLATION_SCORE.get(a["cancellation_policy"], 0.5)
        if prefs.get("needs_flexible_cancellation"):
            return base
        return round(0.6 + 0.4 * base, 2)

    def _accessibility_fit(self, a: dict[str, Any], prefs: dict[str, Any]) -> float:
        if prefs.get("accessibility_required"):
            return 1.0 if a["accessibility_features"] else 0.1
        return 0.7

    def _family_fit(self, a: dict[str, Any], prefs: dict[str, Any]) -> float:
        if prefs.get("has_children"):
            return 1.0 if a["family_friendly"] else 0.3
        return 0.6

    def _business_fit(self, a: dict[str, Any], prefs: dict[str, Any]) -> float:
        if prefs.get("is_business_trip"):
            return 1.0 if a["business_friendly"] else 0.3
        return 0.6

    def _dna_and_goal_adjustment(
        self,
        a: dict[str, Any],
        dna: dict[str, Any] | None,
        goal_type: str | None,
    ) -> tuple[float, list[str]]:
        adjustment = 0.0
        notes: list[str] = []

        traits = (dna or {}).get("traits", {})

        if traits.get("luxury_orientation", 0) > 0.5 and a["star_rating"] >= 4:
            adjustment += 0.08
            notes.append("Luxury-oriented traveller — high star rating boosted.")

        if traits.get("budget_consciousness", 0) > 0.5 and a["nightly_price"] <= a.get("_price_anchor", a["nightly_price"]):
            adjustment += 0.06
            notes.append("Budget-conscious traveller — below-average nightly rate boosted.")

        if traits.get("family_orientation", 0) > 0.5 and a["family_friendly"]:
            adjustment += 0.06
            notes.append("Family-oriented traveller — family-friendly property boosted.")

        if traits.get("business_orientation", 0) > 0.5 and a["business_friendly"]:
            adjustment += 0.06
            notes.append("Business-oriented traveller — business-friendly property boosted.")

        if goal_type == "FAMILY_TRIP" and a["family_friendly"]:
            adjustment += 0.05
            notes.append("Family trip goal — family-friendly property boosted.")

        if goal_type == "BUSINESS_TRAVEL" and a["business_friendly"]:
            adjustment += 0.05
            notes.append("Business travel goal — business-friendly property boosted.")

        return adjustment, notes

    def _persona_scores(self, a: dict[str, Any], breakdown: dict[str, float]) -> dict[str, float]:
        """Independent, persona-weighted scores — used to label options that
        aren't the overall winner but are still the best fit for a segment."""
        value = breakdown["price_fit"] * 0.5 + breakdown["review_score_fit"] * 0.5
        location = a["location_score"]
        comfort = a["comfort_score"] * 0.6 + breakdown["review_score_fit"] * 0.4
        family = (
            (1.0 if a["family_friendly"] else 0.3) * 0.5
            + breakdown["accessibility_fit"] * 0.25
            + a["comfort_score"] * 0.25
        )
        business = (
            (1.0 if a["business_friendly"] else 0.3) * 0.5
            + breakdown["cancellation_flexibility_fit"] * 0.25
            + a["location_score"] * 0.25
        )
        budget = breakdown["price_fit"] * 0.7 + (1.0 - a["comfort_score"]) * 0.3
        return {
            "value": round(value, 2),
            "location": round(location, 2),
            "comfort": round(comfort, 2),
            "family": round(family, 2),
            "business": round(business, 2),
            "budget": round(budget, 2),
        }


accommodation_scorer = AccommodationScorer()
