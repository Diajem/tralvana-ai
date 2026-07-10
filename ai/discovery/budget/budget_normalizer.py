from __future__ import annotations

from typing import Any

# Objective, preference-independent scores per style — the same for every
# traveller, mirroring how ai/discovery/destinations/destination_normalizer.py
# derives budget_score from budget_tier. See docs/DISCOVERY_LAYER_PATTERN.md.
_AFFORDABILITY_SCORE: dict[str, float] = {
    "backpacker": 1.0, "budget": 0.8, "balanced": 0.6, "comfort": 0.35, "luxury": 0.15,
}
_COMFORT_SCORE: dict[str, float] = {
    "backpacker": 0.15, "budget": 0.35, "balanced": 0.6, "comfort": 0.85, "luxury": 1.0,
}
# How stable/predictable a tier's actual cost tends to be in practice.
# Backpacker/budget tiers depend on informal, availability-driven pricing
# (hostel beds, local transport); luxury has the most optional add-ons.
# Balanced/comfort sit on the most standardised, well-documented price bands.
_COST_CERTAINTY_SCORE: dict[str, float] = {
    "backpacker": 0.55, "budget": 0.70, "balanced": 0.85, "comfort": 0.80, "luxury": 0.60,
}
# How suitable a tier is for travelling with children — independent of any
# specific traveller's preferences (a property of the tier itself: does it
# imply hostel dorms, informal transport, unpredictable schedules, etc.).
_FAMILY_SUITABILITY_SCORE: dict[str, float] = {
    "backpacker": 0.30, "budget": 0.50, "balanced": 0.85, "comfort": 1.0, "luxury": 0.70,
}

_ACCOMMODATION_SHARE = 0.45
_FOOD_SHARE = 0.25
_ACTIVITIES_SHARE = 0.20
_MISC_SHARE = 0.10


class BudgetNormalizer:
    """
    Converts a raw MockBudgetProvider record into the canonical internal
    schema, and computes the objective (preference-independent) scores every
    downstream stage relies on: affordability_score, comfort_score,
    cost_certainty_score, family_suitability_score. These are properties of
    the budget tier itself — the same for every traveller. Also computes the
    full cost breakdown (flights, accommodation, food, activities, misc,
    total) using the same accommodation/food/activities/misc shares as
    ai/planning/budget_estimator.py, so a Budget Intelligence option and a
    Trip Plan's budget estimate stay consistent for the same inputs.
    """

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any]:
        style = raw["budget_style"]
        adults = raw["adults"]
        children = raw["children"]
        duration_days = raw["duration_days"]
        child_factor = raw["_child_cost_factor"]

        weighted_travellers = adults + children * child_factor
        daily_total = raw["daily_pp_usd"] * weighted_travellers
        flight_total = raw["flight_pp_usd"] * weighted_travellers

        accommodation = round(daily_total * _ACCOMMODATION_SHARE * duration_days)
        food = round(daily_total * _FOOD_SHARE * duration_days)
        activities = round(daily_total * _ACTIVITIES_SHARE * duration_days)
        misc = round(daily_total * _MISC_SHARE * duration_days)
        flights = round(flight_total)
        total = flights + accommodation + food + activities + misc

        return {
            "destination": raw["destination"],
            "region": raw["region"],
            "budget_style": style,
            "duration_days": duration_days,
            "adults": adults,
            "children": children,
            "cabin_class": raw["cabin_class"],
            "daily_cost_usd": round(daily_total),
            "flight_cost_usd": flights,
            "accommodation_usd": accommodation,
            "food_usd": food,
            "activities_usd": activities,
            "misc_usd": misc,
            "total_cost_usd": total,
            "cost_per_day_usd": round(total / max(duration_days, 1)),
            "cost_per_person_usd": round(total / max(adults + children, 1)),
            "currency": "USD",
            "affordability_score": _AFFORDABILITY_SCORE[style],
            "comfort_score": _COMFORT_SCORE[style],
            "cost_certainty_score": _COST_CERTAINTY_SCORE[style],
            "family_suitability_score": _FAMILY_SUITABILITY_SCORE[style],
        }


budget_normalizer = BudgetNormalizer()
