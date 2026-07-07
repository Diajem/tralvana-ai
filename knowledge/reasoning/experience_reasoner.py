from __future__ import annotations

from typing import TYPE_CHECKING, Any

from knowledge.graph.relationships import RelationshipType

if TYPE_CHECKING:
    from knowledge.graph.knowledge_graph import KnowledgeGraph

# Interest tag → entity types and attraction tags that match
_INTEREST_TAGS: dict[str, list[str]] = {
    "culture":    ["cultural", "historic", "religious", "art"],
    "nature":     ["natural"],
    "adventure":  ["natural", "sport", "extreme"],
    "food_drink": ["food", "restaurant"],
    "sport":      ["sport", "football"],
    "beach":      ["beach", "coastal"],
    "city":       ["urban", "modern"],
    "history":    ["historic", "history"],
    "wellness":   ["spa", "wellness"],
    "luxury":     ["luxury"],
    "business":   ["business", "conference"],
}


class ExperienceReasoner:
    """
    Matches traveller interests to experiences available at a destination.

    Sprint 1: tag-based matching against knowledge graph entities.
    Sprint 3+: ML-ranked personalised experience scoring.
    """

    def __init__(self, graph: KnowledgeGraph | None = None) -> None:
        if graph is None:
            from knowledge import knowledge_graph
            self._graph = knowledge_graph
        else:
            self._graph = graph

    def reason(
        self,
        destination: str,
        traveller_profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        prefs = (traveller_profile or {}).get("preferences", {})
        interests: list[str] = prefs.get("travel_interests", [])

        city = self._graph.find_node_by_name("City", destination)
        if city is None:
            return self._unknown(destination)

        matched_attractions = self._match_attractions(city.id, interests)
        matched_museums = self._match_museums(city.id, interests)
        matched_restaurants = self._match_restaurants(city.id, prefs)
        matched_events = self._all_events(city.id)
        football = self._football_clubs(city.id) if "sport" in interests else []

        interest_tags = [t for interest in interests for t in _INTEREST_TAGS.get(interest, [])]

        return {
            "destination_found": True,
            "destination": destination,
            "interests_matched": interests,
            "matched_attractions": matched_attractions,
            "matched_museums": matched_museums,
            "matched_restaurants": matched_restaurants,
            "events": matched_events,
            "football_clubs": football,
            "personalisation_note": (
                f"Experiences filtered for: {', '.join(interests) or 'general traveller'}."
            ),
            "confidence": 0.65,
            "reasoning_source": "knowledge_graph_v1_tag_match",
        }

    # ------------------------------------------------------------------

    def _match_attractions(self, city_id: str, interests: list[str]) -> list[dict]:
        interest_tags = {
            tag
            for interest in interests
            for tag in _INTEREST_TAGS.get(interest, [])
        }
        edges = self._graph.get_inbound_edges(city_id, RelationshipType.NEAR)
        results = []
        for e in edges:
            node = self._graph.get_node(e.source_id)
            if node and self._graph.get_node_type(e.source_id) == "Attraction":
                overlap = set(node.tags) & interest_tags
                relevance = len(overlap) / max(len(interest_tags), 1)
                results.append({
                    "name": node.name,
                    "type": node.attraction_type,
                    "tags": node.tags,
                    "relevance": round(relevance, 2),
                })
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:5]

    def _match_museums(self, city_id: str, interests: list[str]) -> list[dict]:
        culture_focused = any(i in interests for i in ("culture", "history", "art"))
        edges = self._graph.get_inbound_edges(city_id, RelationshipType.LOCATED_IN)
        results = []
        for e in edges:
            node = self._graph.get_node(e.source_id)
            if node and self._graph.get_node_type(e.source_id) == "Museum":
                results.append({"name": node.name, "category": node.category, "tags": node.tags})
        return results[:3] if culture_focused else results[:1]

    def _match_restaurants(self, city_id: str, prefs: dict) -> list[dict]:
        meal = prefs.get("meal", "standard")
        budget_style = prefs.get("budget_style", "balanced")
        tier_map = {
            "backpacker": "budget", "budget": "budget",
            "balanced": "mid-range", "comfort": "luxury", "luxury": "luxury",
        }
        preferred_tier = tier_map.get(budget_style, "mid-range")

        edges = self._graph.get_inbound_edges(city_id, RelationshipType.BELONGS_TO)
        results = []
        for e in edges:
            node = self._graph.get_node(e.source_id)
            if node and self._graph.get_node_type(e.source_id) == "Restaurant":
                results.append({
                    "name": node.name,
                    "cuisine": node.cuisine,
                    "tier": node.price_tier,
                    "tags": node.tags,
                })
        tier_match = [r for r in results if r["tier"] == preferred_tier]
        return (tier_match or results)[:3]

    def _all_events(self, city_id: str) -> list[dict]:
        edges = self._graph.get_inbound_edges(city_id, RelationshipType.PART_OF)
        results = []
        for e in edges:
            node = self._graph.get_node(e.source_id)
            if node and self._graph.get_node_type(e.source_id) == "Event":
                results.append({"name": node.name, "type": node.event_type, "month": node.month, "tags": node.tags})
        return results

    def _football_clubs(self, city_id: str) -> list[dict]:
        edges = self._graph.get_inbound_edges(city_id, RelationshipType.BELONGS_TO)
        results = []
        for e in edges:
            node = self._graph.get_node(e.source_id)
            if node and self._graph.get_node_type(e.source_id) == "FootballClub":
                results.append({"name": node.name, "league": node.league, "stadium": node.stadium})
        return results

    def _unknown(self, destination: str) -> dict[str, Any]:
        return {
            "destination_found": False,
            "destination_queried": destination,
            "message": f"'{destination}' is not yet in the TravelOS Knowledge Graph.",
            "reasoning_source": "knowledge_graph_v1_tag_match",
        }


experience_reasoner = ExperienceReasoner()
