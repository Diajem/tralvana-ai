from __future__ import annotations


from ai.intelligence.knowledge.relationships import RelationshipType
from ai.intelligence.reasoning.base_reasoner import BaseReasoner, ReasoningResult

_INTEREST_ATTRACTION_TAGS: dict[str, list[str]] = {
    "culture":    ["cultural", "historic", "religious", "art"],
    "nature":     ["natural", "wildlife"],
    "adventure":  ["natural", "sport", "extreme"],
    "food_drink": ["food", "restaurant"],
    "sport":      ["sport", "football"],
    "beach":      ["beach", "coastal"],
    "city":       ["urban", "modern"],
    "history":    ["historic", "history", "ancient"],
    "wellness":   ["spa", "wellness"],
    "luxury":     ["luxury"],
    "business":   ["business", "conference"],
    "religious":  ["religious", "pilgrimage"],
    "pilgrimage": ["religious", "pilgrimage"],
    "heritage":   ["cultural", "history", "african"],
    "diaspora":   ["cultural", "african-heritage"],
}


class ExperienceReasoner(BaseReasoner):
    """
    Matches traveller interests to experiences at the destination via tag overlap.

    Sprint 1: tag-based graph traversal.
    Sprint 3+: ML-ranked personalised scoring using collaborative filtering.
    """

    def reason(self, destination: str, traveller_profile: dict | None = None, **_) -> ReasoningResult:
        city, _ = self._city_and_country(destination)
        if city is None:
            return self._not_found(destination, f"'{destination}' is not in the knowledge graph.")

        prefs = (traveller_profile or {}).get("preferences", {})
        interests: list[str] = prefs.get("travel_interests", [])
        interest_tags: set[str] = {tag for i in interests for tag in _INTEREST_ATTRACTION_TAGS.get(i, [])}

        attractions = self._rank_attractions(city.id, interest_tags)
        museums = self._museums(city.id, interests)
        restaurants = self._restaurants(city.id, prefs)
        events = self._events(city.id)
        clubs = self._clubs(city.id) if "sport" in interests else []
        venues = self._venues(city.id) if "sport" in interests else []

        return ReasoningResult(
            reasoner_name="ExperienceReasoner",
            subject=destination,
            success=True,
            confidence=0.65,
            data={
                "interests_applied": interests,
                "matched_attractions": attractions,
                "museums": museums,
                "restaurants": restaurants,
                "events": events,
                "football_clubs": clubs,
                "sports_venues": venues,
                "personalisation_note": (
                    f"Experiences curated for: {', '.join(interests) or 'general traveller'}."
                ),
            },
            assumptions=["Tag-based matching used — exact interest overlap may vary"],
            limitations=["Sprint 1 tag matching; no ranked collaborative filtering yet"],
        )

    # ------------------------------------------------------------------

    def _rank_attractions(self, city_id: str, interest_tags: set[str]) -> list[dict]:
        attractions = self._ks.get_connected_entities(city_id, "Attraction", RelationshipType.NEAR, "inbound")
        scored = []
        for a in attractions:
            overlap = set(a.tags) & interest_tags
            relevance = len(overlap) / max(len(interest_tags), 1)
            scored.append({"name": a.name, "type": a.attraction_type, "tags": a.tags, "relevance": round(relevance, 2)})
        return sorted(scored, key=lambda x: x["relevance"], reverse=True)[:5]

    def _museums(self, city_id: str, interests: list[str]) -> list[dict]:
        culture_focused = any(i in interests for i in ("culture", "history", "art", "heritage"))
        museums = self._ks.get_connected_entities(city_id, "Museum", RelationshipType.LOCATED_IN, "inbound")
        return [{"name": m.name, "category": m.category, "tags": m.tags} for m in museums[:(3 if culture_focused else 1)]]

    def _restaurants(self, city_id: str, prefs: dict) -> list[dict]:
        tier_map = {"backpacker": "budget", "budget": "budget", "balanced": "mid-range", "comfort": "luxury", "luxury": "luxury"}
        pref_tier = tier_map.get(prefs.get("budget_style", "balanced"), "mid-range")
        restaurants = self._ks.get_connected_entities(city_id, "Restaurant", RelationshipType.BELONGS_TO, "inbound")
        match = [r for r in restaurants if r.price_tier == pref_tier]
        chosen = (match or restaurants)[:3]
        return [{"name": r.name, "cuisine_id": r.cuisine_id, "tier": r.price_tier} for r in chosen]

    def _events(self, city_id: str) -> list[dict]:
        events = self._ks.get_connected_entities(city_id, "Event", RelationshipType.PART_OF, "inbound")
        return [{"name": e.name, "type": e.event_type, "month": e.month, "tags": e.tags} for e in events]

    def _clubs(self, city_id: str) -> list[dict]:
        clubs = self._ks.get_connected_entities(city_id, "FootballClub", RelationshipType.PLAYS_IN, "inbound")
        return [{"name": c.name, "league": c.league, "stadium_id": c.stadium_id} for c in clubs]

    def _venues(self, city_id: str) -> list[dict]:
        venues = self._ks.get_connected_entities(city_id, "SportsVenue", RelationshipType.HOSTS, "outbound")
        return [{"name": v.name, "type": v.venue_type, "capacity": v.capacity} for v in venues]


experience_reasoner = ExperienceReasoner()
