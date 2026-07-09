from __future__ import annotations

from typing import Any

# Raw provider vocabulary -> canonical DestinationType values.
_TYPE_MAP: dict[str, str] = {
    "city": "CITY",
    "neighbourhood": "NEIGHBOURHOOD",
    "attraction": "ATTRACTION",
    "museum": "MUSEUM",
    "food_district": "FOOD_DISTRICT",
    "football_venue": "FOOTBALL_VENUE",
    "shopping_district": "SHOPPING_DISTRICT",
    "beach": "BEACH",
    "nature_area": "NATURE_AREA",
    "historic_site": "HISTORIC_SITE",
    "transport_hub": "TRANSPORT_HUB",
    "nightlife_area": "NIGHTLIFE_AREA",
}

_BUDGET_TIER_SCORE: dict[str, float] = {
    "budget": 1.0, "moderate": 0.7, "expensive": 0.4, "luxury": 0.2,
}

_CULTURE_TYPES = {"MUSEUM", "HISTORIC_SITE"}
_FAMILY_FRIENDLY_TYPES = {"BEACH", "NATURE_AREA", "ATTRACTION", "NEIGHBOURHOOD"}
_FAMILY_UNFRIENDLY_TYPES = {"NIGHTLIFE_AREA"}


class DestinationNormalizer:
    """
    Converts a raw MockDestinationProvider record into the canonical internal
    schema, and computes the objective (preference-independent) scores every
    downstream stage relies on: transport_access_score, food_score,
    culture_score, football_score, nightlife_score, family_score,
    safety_score, budget_score, season_score. These are properties of the
    destination option itself — the same for every traveller. See
    docs/DISCOVERY_LAYER_PATTERN.md.

    budget_score is affordability, not cost: 1.0 = very affordable,
    0.0 = very expensive. season_score defaults to a neutral 0.6 when no
    travel month is supplied — it becomes traveller-specific input only in
    that one case, resolved before scoring rather than inside it.
    """

    def normalize(self, raw: dict[str, Any], travel_month: int | None = None) -> dict[str, Any]:
        destination_type = _TYPE_MAP.get(raw["place_type"], "ATTRACTION")
        tags = set(raw.get("tags", []))

        return {
            "city": raw["city"],
            "country": raw["country"],
            "region": raw["region"],
            "neighbourhood": raw["name"] if destination_type != "CITY" else "",
            "destination_type": destination_type,
            "name": raw["name"],
            "description": raw["description"],
            "best_for": raw["best_for"],
            "distance_from_centre": float(raw["distance_from_centre_km"]),
            "transport_access_score": self._transport_score(raw, destination_type),
            "food_score": self._food_score(raw, destination_type, tags),
            "culture_score": self._culture_score(raw, destination_type, tags),
            "football_score": self._football_score(raw, destination_type, tags),
            "nightlife_score": self._nightlife_score(destination_type, tags),
            "family_score": self._family_score(destination_type, tags),
            "safety_score": round(min(max(raw["safety_rating"] / 10, 0.0), 1.0), 2),
            "budget_score": _BUDGET_TIER_SCORE.get(raw["budget_tier"], 0.6),
            "season_score": self._season_score(raw, travel_month),
            "_tags": list(tags),
            "_popularity": raw["popularity"],
        }

    # ------------------------------------------------------------------

    def _transport_score(self, raw: dict[str, Any], destination_type: str) -> float:
        base = raw["transport_rating"] / 10
        if destination_type == "TRANSPORT_HUB":
            return round(min(1.0, base + 0.2), 2)
        distance_penalty = min(0.3, raw["distance_from_centre_km"] / 50)
        return round(min(max(base - distance_penalty, 0.0), 1.0), 2)

    def _food_score(self, raw: dict[str, Any], destination_type: str, tags: set[str]) -> float:
        base = raw["food_scene_rating"] / 10
        if destination_type == "FOOD_DISTRICT":
            return round(min(1.0, base + 0.15), 2)
        if "food" in tags:
            return round(min(1.0, base), 2)
        return round(base * 0.5, 2)

    def _culture_score(self, raw: dict[str, Any], destination_type: str, tags: set[str]) -> float:
        base = raw["culture_rating"] / 10
        if destination_type in _CULTURE_TYPES or {"culture", "heritage"} & tags:
            return round(min(1.0, base + 0.1), 2)
        return round(base * 0.5, 2)

    def _football_score(self, raw: dict[str, Any], destination_type: str, tags: set[str]) -> float:
        if destination_type == "FOOTBALL_VENUE" or "football" in tags:
            return round(min(1.0, raw["football_reputation"] / 10 + 0.3), 2)
        return round(raw["football_reputation"] / 10 * 0.4, 2)

    def _nightlife_score(self, destination_type: str, tags: set[str]) -> float:
        if destination_type == "NIGHTLIFE_AREA" or "nightlife" in tags:
            return 0.9
        return 0.3

    def _family_score(self, destination_type: str, tags: set[str]) -> float:
        if "family" in tags:
            return 0.9
        if destination_type in _FAMILY_UNFRIENDLY_TYPES:
            return 0.2
        if destination_type in _FAMILY_FRIENDLY_TYPES:
            return 0.65
        return 0.5

    def _season_score(self, raw: dict[str, Any], travel_month: int | None) -> float:
        if not travel_month:
            return 0.6
        return 1.0 if travel_month in raw["peak_months"] else 0.5


destination_normalizer = DestinationNormalizer()
