from __future__ import annotations

from typing import Any

from ai.discovery.budget.mock_budget_provider import STYLES

# Dimension weights — must sum to 1.0. Kept explicit so scoring stays
# explainable: every dimension's contribution can be read straight off
# SCORE_WEIGHTS. cap_fit dominates because staying within the traveller's
# actual budget is the entire point of this module — the other Discovery
# modules treat budget_style as one input among several; here it IS the
# candidate set, so the traveller's hard cap has to carry the most weight.
SCORE_WEIGHTS: dict[str, float] = {
    "cap_fit": 0.40,
    "style_fit": 0.25,
    "affordability_fit": 0.20,
    "family_fit": 0.15,
}

_NEUTRAL_CAP_FIT = 0.6
_NEUTRAL_FAMILY_FIT = 0.6
_PERSONA_MIN_FAMILY_SUITABILITY = 0.7


class BudgetScorer:
    """
    Deterministic 0.0-1.0 match scoring for a single normalized budget
    option. Mirrors ai/discovery/flights/flight_scorer.py's and
    ai/discovery/destinations/destination_scorer.py's shape: every sub-score
    is a simple, explainable formula over normalized fields and traveller
    preferences, plus a DNA/goal-type adjustment layer.
    """

    def score(
        self,
        option: dict[str, Any],
        preferences: dict[str, Any],
        dna: dict[str, Any] | None = None,
        goal_type: str | None = None,
    ) -> dict[str, Any]:
        breakdown = {
            "cap_fit": self._cap_fit(option, preferences),
            "style_fit": self._style_fit(option, preferences),
            "affordability_fit": self._affordability_fit(option, preferences),
            "family_fit": self._family_fit(option, preferences),
        }

        base_score = sum(breakdown[k] * SCORE_WEIGHTS[k] for k in SCORE_WEIGHTS)
        adjustment, dna_notes = self._dna_and_goal_adjustment(option, dna, goal_type)
        match_score = round(min(max(base_score + adjustment, 0.0), 1.0), 2)

        persona_scores = self._persona_scores(option)

        return {
            "match_score": match_score,
            "breakdown": breakdown,
            "adjustment": round(adjustment, 2),
            "dna_notes": dna_notes,
            "persona_scores": persona_scores,
        }

    # ------------------------------------------------------------------

    def _cap_fit(self, option: dict[str, Any], prefs: dict[str, Any]) -> float:
        max_usd = prefs.get("budget_max_usd")
        total = option["total_cost_usd"]
        if not max_usd:
            return _NEUTRAL_CAP_FIT
        if total <= max_usd:
            ratio = total / max_usd
            return round(min(1.0, 0.7 + 0.3 * (1 - ratio)), 2)
        over_ratio = (total - max_usd) / max_usd
        return round(max(0.0, 0.5 - over_ratio), 2)

    def _style_fit(self, option: dict[str, Any], prefs: dict[str, Any]) -> float:
        preferred = prefs.get("budget_style", "balanced")
        if preferred not in STYLES:
            preferred = "balanced"
        distance = abs(STYLES.index(option["budget_style"]) - STYLES.index(preferred))
        return {0: 1.0, 1: 0.7, 2: 0.45, 3: 0.25}.get(distance, 0.1)

    def _affordability_fit(self, option: dict[str, Any], prefs: dict[str, Any]) -> float:
        budget_style = prefs.get("budget_style", "balanced")
        if budget_style in ("backpacker", "budget"):
            return option["affordability_score"]
        return round(0.5 + 0.5 * option["affordability_score"], 2)

    def _family_fit(self, option: dict[str, Any], prefs: dict[str, Any]) -> float:
        if prefs.get("has_children"):
            return option["family_suitability_score"]
        return _NEUTRAL_FAMILY_FIT

    def _dna_and_goal_adjustment(
        self,
        option: dict[str, Any],
        dna: dict[str, Any] | None,
        goal_type: str | None,
    ) -> tuple[float, list[str]]:
        adjustment = 0.0
        notes: list[str] = []

        traits = (dna or {}).get("traits", {})
        style = option["budget_style"]

        if traits.get("budget_consciousness", 0) > 0.5 and style in ("backpacker", "budget"):
            adjustment += 0.06
            notes.append("Budget-conscious traveller — a leaner tier boosted.")

        if traits.get("luxury_orientation", 0) > 0.5 and style in ("comfort", "luxury"):
            adjustment += 0.08
            notes.append("Luxury-oriented traveller — a higher-comfort tier boosted.")

        if traits.get("business_orientation", 0) > 0.5 and style in ("comfort", "luxury"):
            adjustment += 0.05
            notes.append("Business-oriented traveller — a more reliable, comfortable tier boosted.")

        if (
            traits.get("family_orientation", 0) > 0.5
            and option["family_suitability_score"] >= _PERSONA_MIN_FAMILY_SUITABILITY
        ):
            adjustment += 0.06
            notes.append("Family-oriented traveller — a family-suitable tier boosted.")

        if goal_type == "BUSINESS_TRAVEL" and style in ("comfort", "luxury"):
            adjustment += 0.08
            notes.append("Business travel goal — a higher-reliability tier boosted.")

        if goal_type == "FAMILY_TRIP" and option["family_suitability_score"] >= _PERSONA_MIN_FAMILY_SUITABILITY:
            adjustment += 0.06
            notes.append("Family trip goal — a family-suitable tier boosted.")

        if goal_type in ("ROMANTIC_TRIP", "RELAXATION") and style in ("comfort", "luxury"):
            adjustment += 0.05
            notes.append(f"{goal_type.replace('_', ' ').title()} goal — a more comfortable tier boosted.")

        if goal_type == "ADVENTURE" and style in ("backpacker", "budget"):
            adjustment += 0.05
            notes.append("Adventure travel goal — a leaner, flexible tier boosted.")

        return adjustment, notes

    def _persona_scores(self, option: dict[str, Any]) -> dict[str, float]:
        """Independent, persona-weighted scores — used to label options that
        aren't the overall winner but are still the best fit for a segment."""
        value = round(option["affordability_score"] * 0.5 + option["comfort_score"] * 0.5, 2)
        family = round(option["family_suitability_score"], 2)
        return {"value": value, "family": family}


budget_scorer = BudgetScorer()
