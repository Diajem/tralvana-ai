from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from knowledge.graph.entities import TravellerDNA


class DNAType(str, Enum):
    EXPLORER = "Explorer"
    LUXURY = "Luxury"
    BUDGET = "Budget"
    FOOTBALL_TRAVELLER = "Football Traveller"
    FAMILY_TRAVELLER = "Family Traveller"
    BUSINESS_TRAVELLER = "Business Traveller"
    ADVENTURE_TRAVELLER = "Adventure Traveller"
    FOOD_TRAVELLER = "Food Traveller"
    PHOTOGRAPHY_TRAVELLER = "Photography Traveller"
    DIGITAL_NOMAD = "Digital Nomad"


# ---------------------------------------------------------------------------
# Trait definitions
# ---------------------------------------------------------------------------

_TRAITS = [
    "adventure_seeking",
    "luxury_orientation",
    "budget_consciousness",
    "cultural_curiosity",
    "food_focus",
    "sport_focus",
    "business_orientation",
    "family_orientation",
    "digital_mobility",
    "photography_tendency",
]


class DNAInferenceService:
    """
    Deterministic Traveller DNA inference from a TIP profile.

    Sprint 1: scoring rules based on profile fields.
    Sprint 3+: ML-based inference trained on anonymised trip data.
    """

    def infer(self, profile: dict[str, Any]) -> TravellerDNA:
        traveller_id = profile.get("id", "unknown")
        traits = self._score_traits(profile)
        dna_scores = self._score_dna_types(profile, traits)

        ranked = sorted(dna_scores.items(), key=lambda x: x[1], reverse=True)
        primary = ranked[0][0]
        primary_score = ranked[0][1]

        # Secondary types: score > 0.15 and not primary
        secondary = [name for name, score in ranked[1:] if score > 0.15]

        return TravellerDNA(
            traveller_id=traveller_id,
            primary_type=primary,
            secondary_types=secondary,
            confidence=round(min(primary_score, 1.0), 2),
            traits={k: round(min(v, 1.0), 2) for k, v in traits.items()},
            inferred_at=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------

    def _score_traits(self, profile: dict[str, Any]) -> dict[str, float]:
        prefs = profile.get("preferences", {})
        budget_style = prefs.get("budget_style", "balanced")
        cabin = prefs.get("cabin_class", "economy")
        interests: set[str] = set(prefs.get("travel_interests", []))
        accommodation = prefs.get("accommodation_type", "hotel")
        meal = prefs.get("meal", "standard")
        loyalty = profile.get("loyalty", {})
        has_airline_loyalty = bool(loyalty.get("airline_programs"))

        scores: dict[str, float] = {t: 0.0 for t in _TRAITS}

        # adventure_seeking
        if "adventure" in interests: scores["adventure_seeking"] += 0.5
        if "nature" in interests:    scores["adventure_seeking"] += 0.25
        if "sport" in interests:     scores["adventure_seeking"] += 0.15
        if budget_style in ("backpacker", "budget"): scores["adventure_seeking"] += 0.1

        # luxury_orientation
        if cabin == "first":             scores["luxury_orientation"] += 0.4
        if cabin == "business":          scores["luxury_orientation"] += 0.2
        if budget_style == "luxury":     scores["luxury_orientation"] += 0.4
        if budget_style == "comfort":    scores["luxury_orientation"] += 0.15
        if "luxury" in interests:        scores["luxury_orientation"] += 0.25
        if accommodation == "resort":    scores["luxury_orientation"] += 0.1

        # budget_consciousness
        if budget_style == "backpacker":         scores["budget_consciousness"] += 0.5
        if budget_style == "budget":             scores["budget_consciousness"] += 0.4
        if accommodation == "hostel":            scores["budget_consciousness"] += 0.3
        if cabin == "economy" and budget_style in ("backpacker", "budget"):
            scores["budget_consciousness"] += 0.15

        # cultural_curiosity
        if "culture" in interests:   scores["cultural_curiosity"] += 0.4
        if "city" in interests:      scores["cultural_curiosity"] += 0.2
        if "history" in interests:   scores["cultural_curiosity"] += 0.3
        if len(interests) >= 4:      scores["cultural_curiosity"] += 0.1

        # food_focus
        if "food_drink" in interests:                              scores["food_focus"] += 0.5
        if meal in ("halal", "kosher", "vegan", "vegetarian"):    scores["food_focus"] += 0.25
        if "culture" in interests:                                 scores["food_focus"] += 0.1

        # sport_focus
        if "sport" in interests:    scores["sport_focus"] += 0.5
        if "adventure" in interests:scores["sport_focus"] += 0.15

        # business_orientation
        if "business" in interests:  scores["business_orientation"] += 0.4
        if cabin == "business":       scores["business_orientation"] += 0.3
        if has_airline_loyalty:       scores["business_orientation"] += 0.2
        if budget_style in ("comfort", "luxury"): scores["business_orientation"] += 0.1

        # family_orientation
        if accommodation == "resort":  scores["family_orientation"] += 0.3
        if "beach" in interests:       scores["family_orientation"] += 0.2
        if "wellness" in interests:    scores["family_orientation"] += 0.15

        # digital_mobility
        if "city" in interests:                     scores["digital_mobility"] += 0.3
        if budget_style in ("budget", "balanced"):  scores["digital_mobility"] += 0.2
        if accommodation == "apartment":             scores["digital_mobility"] += 0.35
        if cabin == "economy":                       scores["digital_mobility"] += 0.1

        # photography_tendency
        if "nature" in interests:    scores["photography_tendency"] += 0.3
        if "culture" in interests:   scores["photography_tendency"] += 0.25
        if "city" in interests:      scores["photography_tendency"] += 0.2
        if "adventure" in interests: scores["photography_tendency"] += 0.1

        return scores

    def _score_dna_types(
        self, profile: dict[str, Any], traits: dict[str, float]
    ) -> dict[str, float]:
        prefs = profile.get("preferences", {})
        interests: set[str] = set(prefs.get("travel_interests", []))

        scores: dict[str, float] = {}

        scores[DNAType.LUXURY.value] = (
            traits["luxury_orientation"] * 0.7
        )

        scores[DNAType.BUDGET.value] = (
            traits["budget_consciousness"] * 0.8
        )

        scores[DNAType.BUSINESS_TRAVELLER.value] = (
            traits["business_orientation"] * 0.8
        )

        scores[DNAType.FOOTBALL_TRAVELLER.value] = (
            traits["sport_focus"] * 0.9
        )

        scores[DNAType.FAMILY_TRAVELLER.value] = (
            traits["family_orientation"] * 0.85
        )

        scores[DNAType.ADVENTURE_TRAVELLER.value] = (
            traits["adventure_seeking"] * 0.85
        )

        scores[DNAType.FOOD_TRAVELLER.value] = (
            traits["food_focus"] * 0.9
        )

        scores[DNAType.PHOTOGRAPHY_TRAVELLER.value] = (
            traits["photography_tendency"] * 0.8
        )

        scores[DNAType.DIGITAL_NOMAD.value] = (
            traits["digital_mobility"] * 0.85
        )

        # Explorer: breadth of interests + moderate budget orientation
        n_interests = len(interests)
        explorer_score = 0.0
        if n_interests >= 5:   explorer_score += 0.5
        elif n_interests >= 3: explorer_score += 0.3
        elif n_interests >= 2: explorer_score += 0.15
        explorer_score += traits["cultural_curiosity"] * 0.3
        scores[DNAType.EXPLORER.value] = explorer_score

        return scores


dna_inference_service = DNAInferenceService()
