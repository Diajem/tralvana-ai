from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ai.intelligence.knowledge.entities import TravellerDNA
from ai.intelligence.traveller_dna.dna_types import DNA_DESCRIPTIONS, DNAType, TRAITS


class TravellerDNAInferenceService:
    """
    Deterministic Traveller DNA inference from a TIP profile dict.

    Two-phase algorithm:
      1. Score 12 raw traits (0.0–1.0) from profile fields.
      2. Map trait scores to 12 DNA type scores; pick primary + secondaries.

    Sprint 1: rule-based on profile fields.
    Sprint 3+: replace with an ML model trained on anonymised trip history.
    """

    SECONDARY_THRESHOLD = 0.15

    def infer(self, profile: dict[str, Any]) -> TravellerDNA:
        traveller_id = profile.get("id", "unknown")
        traits = self._score_traits(profile)
        dna_scores = self._score_dna(profile, traits)

        ranked = sorted(dna_scores.items(), key=lambda x: x[1], reverse=True)
        primary, primary_score = ranked[0]
        secondary = [
            name for name, score in ranked[1:] if score > self.SECONDARY_THRESHOLD
        ]

        return TravellerDNA(
            traveller_id=traveller_id,
            primary_type=primary,
            secondary_types=secondary,
            confidence=round(min(primary_score, 1.0), 2),
            traits={k: round(min(v, 1.0), 2) for k, v in traits.items()},
            inferred_at=datetime.now(timezone.utc).isoformat(),
        )

    def describe(self, dna_type: str) -> str:
        return DNA_DESCRIPTIONS.get(dna_type, "Travel archetype not found.")

    # ------------------------------------------------------------------
    # Phase 1: trait scoring
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

        s: dict[str, float] = {t: 0.0 for t in TRAITS}

        # adventure_seeking
        if "adventure" in interests:
            s["adventure_seeking"] += 0.50
        if "nature" in interests:
            s["adventure_seeking"] += 0.25
        if "sport" in interests:
            s["adventure_seeking"] += 0.15
        if budget_style in ("backpacker", "budget"):
            s["adventure_seeking"] += 0.10

        # luxury_orientation
        if cabin == "first":
            s["luxury_orientation"] += 0.40
        if cabin == "business":
            s["luxury_orientation"] += 0.20
        if budget_style == "luxury":
            s["luxury_orientation"] += 0.40
        if budget_style == "comfort":
            s["luxury_orientation"] += 0.15
        if "luxury" in interests:
            s["luxury_orientation"] += 0.25
        if accommodation == "resort":
            s["luxury_orientation"] += 0.10

        # budget_consciousness
        if budget_style == "backpacker":
            s["budget_consciousness"] += 0.50
        if budget_style == "budget":
            s["budget_consciousness"] += 0.40
        if accommodation == "hostel":
            s["budget_consciousness"] += 0.30
        if cabin == "economy" and budget_style in ("backpacker", "budget"):
            s["budget_consciousness"] += 0.15

        # cultural_curiosity
        if "culture" in interests:
            s["cultural_curiosity"] += 0.40
        if "history" in interests:
            s["cultural_curiosity"] += 0.30
        if "city" in interests:
            s["cultural_curiosity"] += 0.20
        if len(interests) >= 4:
            s["cultural_curiosity"] += 0.10

        # food_focus
        if "food_drink" in interests:
            s["food_focus"] += 0.50
        if meal in ("halal", "kosher", "vegan", "vegetarian"):
            s["food_focus"] += 0.25
        if "culture" in interests:
            s["food_focus"] += 0.10

        # sport_focus
        if "sport" in interests:
            s["sport_focus"] += 0.50
        if "adventure" in interests:
            s["sport_focus"] += 0.15

        # business_orientation
        if "business" in interests:
            s["business_orientation"] += 0.40
        if cabin == "business":
            s["business_orientation"] += 0.30
        if has_airline_loyalty:
            s["business_orientation"] += 0.20
        if budget_style in ("comfort", "luxury"):
            s["business_orientation"] += 0.10

        # family_orientation
        if accommodation == "resort":
            s["family_orientation"] += 0.30
        if "beach" in interests:
            s["family_orientation"] += 0.20
        if "wellness" in interests:
            s["family_orientation"] += 0.15

        # digital_mobility
        if "city" in interests:
            s["digital_mobility"] += 0.30
        if budget_style in ("budget", "balanced"):
            s["digital_mobility"] += 0.20
        if accommodation == "apartment":
            s["digital_mobility"] += 0.35
        if cabin == "economy":
            s["digital_mobility"] += 0.10

        # photography_tendency
        if "nature" in interests:
            s["photography_tendency"] += 0.30
        if "culture" in interests:
            s["photography_tendency"] += 0.25
        if "city" in interests:
            s["photography_tendency"] += 0.20
        if "adventure" in interests:
            s["photography_tendency"] += 0.10

        # spiritual_orientation
        if "religious" in interests:
            s["spiritual_orientation"] += 0.40
        if "pilgrimage" in interests:
            s["spiritual_orientation"] += 0.50
        if "spiritual" in interests:
            s["spiritual_orientation"] += 0.35
        if "culture" in interests:
            s["spiritual_orientation"] += 0.10

        # heritage_connection
        if "heritage" in interests:
            s["heritage_connection"] += 0.50
        if "diaspora" in interests:
            s["heritage_connection"] += 0.50
        if "roots" in interests:
            s["heritage_connection"] += 0.40
        if "family" in interests:
            s["heritage_connection"] += 0.20

        return s

    # ------------------------------------------------------------------
    # Phase 2: DNA type scoring
    # ------------------------------------------------------------------

    def _score_dna(
        self, profile: dict[str, Any], traits: dict[str, float]
    ) -> dict[str, float]:
        interests: set[str] = set(
            profile.get("preferences", {}).get("travel_interests", [])
        )
        n = len(interests)

        scores = {
            DNAType.LUXURY_TRAVELLER.value: traits["luxury_orientation"] * 0.80,
            DNAType.BUDGET_TRAVELLER.value: traits["budget_consciousness"] * 0.80,
            DNAType.BUSINESS_TRAVELLER.value: traits["business_orientation"] * 0.80,
            DNAType.FOOTBALL_TRAVELLER.value: traits["sport_focus"] * 0.90,
            DNAType.FAMILY_TRAVELLER.value: traits["family_orientation"] * 0.85,
            DNAType.ADVENTURE_TRAVELLER.value: traits["adventure_seeking"] * 0.85,
            DNAType.FOOD_TRAVELLER.value: traits["food_focus"] * 0.90,
            DNAType.PHOTOGRAPHY_TRAVELLER.value: traits["photography_tendency"] * 0.80,
            DNAType.DIGITAL_NOMAD.value: traits["digital_mobility"] * 0.85,
            DNAType.PILGRIMAGE_TRAVELLER.value: traits["spiritual_orientation"] * 0.90,
            DNAType.DIASPORA_TRAVELLER.value: traits["heritage_connection"] * 0.85,
        }

        # Explorer: breadth + curiosity bonus
        explorer = traits["cultural_curiosity"] * 0.30
        if n >= 5:
            explorer += 0.50
        elif n >= 3:
            explorer += 0.30
        elif n >= 2:
            explorer += 0.15
        scores[DNAType.EXPLORER.value] = explorer

        return scores
