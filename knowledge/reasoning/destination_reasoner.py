from __future__ import annotations

from typing import TYPE_CHECKING, Any

from knowledge.graph.relationships import RelationshipType

if TYPE_CHECKING:
    from knowledge.graph.knowledge_graph import KnowledgeGraph


class DestinationReasoner:
    """
    Aggregates graph knowledge about a destination into a structured summary.

    Sprint 1: reads from in-memory KnowledgeGraph.
    Sprint 4+: replace _graph with a Neo4j/ArangoDB client — callers unchanged.
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
        city = self._graph.find_node_by_name("City", destination)
        if city is None:
            return self._unknown(destination)

        country = self._graph.get_node(city.country_id)
        airports = self._airports_for(city.id)
        hotels = self._hotels_for(city.id, traveller_profile)
        attractions = self._attractions_for(city.id)
        museums = self._museums_for(city.id)
        clubs = self._clubs_for(city.id)
        events = self._events_for(city.id)
        transport = self._transport_for(city.id)
        weather = self._weather_summary(city.id)
        currency = self._currency_for(country) if country else None

        return {
            "destination_found": True,
            "city": {
                "id": city.id,
                "name": city.name,
                "timezone": city.timezone,
                "tags": city.tags,
            },
            "country": {
                "name": country.name if country else "Unknown",
                "iso_code": country.iso_code if country else "",
                "safety_level": country.safety_level if country else "unknown",
                "language": country.languages[0] if country and country.languages else "en",
            },
            "currency": currency,
            "airports": airports,
            "recommended_hotels": hotels,
            "top_attractions": attractions,
            "museums": museums,
            "football_clubs": clubs,
            "events": events,
            "local_transport": transport,
            "weather_overview": weather,
            "reasoning_source": "knowledge_graph_v1",
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _airports_for(self, city_id: str) -> list[dict]:
        edges = self._graph.get_inbound_edges(city_id, RelationshipType.LOCATED_IN)
        results = []
        for e in edges:
            node = self._graph.get_node(e.source_id)
            if node and self._graph.get_node_type(e.source_id) == "Airport":
                results.append({"name": node.name, "iata": node.iata_code})
        return results

    def _hotels_for(self, city_id: str, profile: dict | None) -> list[dict]:
        budget_style = (
            (profile or {}).get("preferences", {}).get("budget_style", "balanced")
        )
        tier_map = {
            "backpacker": "budget", "budget": "budget",
            "balanced": "mid-range", "comfort": "luxury", "luxury": "luxury",
        }
        preferred_tier = tier_map.get(budget_style, "mid-range")

        edges = self._graph.get_inbound_edges(city_id, RelationshipType.BELONGS_TO)
        hotels = []
        for e in edges:
            node = self._graph.get_node(e.source_id)
            if node and self._graph.get_node_type(e.source_id) == "Hotel":
                hotels.append(node)

        # Prefer matching tier, fall back to all
        tier_match = [h for h in hotels if h.price_tier == preferred_tier]
        chosen = (tier_match or hotels)[:3]
        return [
            {"name": h.name, "stars": h.star_rating, "tier": h.price_tier, "amenities": h.amenities}
            for h in chosen
        ]

    def _attractions_for(self, city_id: str) -> list[dict]:
        edges = self._graph.get_inbound_edges(city_id, RelationshipType.NEAR)
        results = []
        for e in edges:
            node = self._graph.get_node(e.source_id)
            if node and self._graph.get_node_type(e.source_id) == "Attraction":
                results.append({"name": node.name, "type": node.attraction_type, "tags": node.tags})
        return results[:5]

    def _museums_for(self, city_id: str) -> list[dict]:
        edges = self._graph.get_inbound_edges(city_id, RelationshipType.LOCATED_IN)
        results = []
        for e in edges:
            node = self._graph.get_node(e.source_id)
            if node and self._graph.get_node_type(e.source_id) == "Museum":
                results.append({"name": node.name, "category": node.category})
        return results[:3]

    def _clubs_for(self, city_id: str) -> list[dict]:
        edges = self._graph.get_inbound_edges(city_id, RelationshipType.BELONGS_TO)
        results = []
        for e in edges:
            node = self._graph.get_node(e.source_id)
            if node and self._graph.get_node_type(e.source_id) == "FootballClub":
                results.append({"name": node.name, "league": node.league, "stadium": node.stadium})
        return results

    def _events_for(self, city_id: str) -> list[dict]:
        edges = self._graph.get_inbound_edges(city_id, RelationshipType.PART_OF)
        results = []
        for e in edges:
            node = self._graph.get_node(e.source_id)
            if node and self._graph.get_node_type(e.source_id) == "Event":
                results.append({"name": node.name, "type": node.event_type, "month": node.month})
        return results[:4]

    def _transport_for(self, city_id: str) -> list[dict]:
        edges = self._graph.get_inbound_edges(city_id, RelationshipType.BELONGS_TO)
        results = []
        for e in edges:
            node = self._graph.get_node(e.source_id)
            if node and self._graph.get_node_type(e.source_id) == "Transport":
                results.append({"name": node.name, "type": node.transport_type})
        return results

    def _weather_summary(self, city_id: str) -> list[dict]:
        edges = self._graph.get_outbound_edges(city_id, RelationshipType.HAS_WEATHER)
        results = []
        for e in edges:
            node = self._graph.get_node(e.target_id)
            if node:
                results.append({
                    "month": node.month,
                    "avg_temp_c": node.avg_temp_c,
                    "condition": node.condition,
                    "season": node.season,
                })
        return sorted(results, key=lambda x: x["month"])

    def _currency_for(self, country: Any) -> dict | None:
        edges = self._graph.get_outbound_edges(country.id, RelationshipType.USES_CURRENCY)
        for e in edges:
            node = self._graph.get_node(e.target_id)
            if node:
                return {"code": node.code, "name": node.name, "symbol": node.symbol}
        return None

    def _unknown(self, destination: str) -> dict[str, Any]:
        return {
            "destination_found": False,
            "destination_queried": destination,
            "message": (
                f"'{destination}' is not yet in the TravelOS Knowledge Graph. "
                "Knowledge graph coverage will expand in Sprint 2."
            ),
            "reasoning_source": "knowledge_graph_v1",
        }


destination_reasoner = DestinationReasoner()
