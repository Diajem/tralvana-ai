from __future__ import annotations

from typing import Any

from ai.intelligence.knowledge.relationships import RelationshipType
from ai.intelligence.reasoning.base_reasoner import BaseReasoner, ReasoningResult


class DestinationReasoner(BaseReasoner):
    """
    Aggregates all graph knowledge about a destination city into one summary.

    Sprint 1: in-memory graph traversal.
    Sprint 4+: replace _ks with Neo4j/Kuzu queries — interface unchanged.
    """

    def reason(self, destination: str, traveller_profile: dict | None = None, **_) -> ReasoningResult:
        city, country = self._city_and_country(destination)
        if city is None:
            return self._not_found(destination, f"'{destination}' is not in the knowledge graph.")

        airports   = self._connected(city.id, "Airport",     RelationshipType.SERVES,      "inbound")
        rail       = self._connected(city.id, "RailStation", RelationshipType.CONNECTS,     "inbound")
        hotels     = self._hotels(city.id, traveller_profile)
        attractions= self._connected(city.id, "Attraction",  RelationshipType.NEAR,         "inbound")[:5]
        museums    = self._connected(city.id, "Museum",      RelationshipType.LOCATED_IN,   "inbound")[:3]
        restaurants= self._connected(city.id, "Restaurant",  RelationshipType.BELONGS_TO,   "inbound")[:3]
        clubs      = self._connected(city.id, "FootballClub",RelationshipType.PLAYS_IN,     "inbound")
        venues     = self._connected(city.id, "SportsVenue", RelationshipType.HOSTS,        "outbound")
        events     = self._connected(city.id, "Event",       RelationshipType.PART_OF,      "inbound")[:4]
        transport  = self._connected(city.id, "Transport",   RelationshipType.BELONGS_TO,   "inbound")
        weather    = self._weather(city.id)
        currency   = self._currency(country)
        region     = self._region(city)

        return ReasoningResult(
            reasoner_name="DestinationReasoner",
            subject=destination,
            success=True,
            confidence=0.82,
            data={
                "city": {"name": city.name, "timezone": city.timezone, "tags": city.tags},
                "region": region,
                "country": {
                    "name": country.name if country else "Unknown",
                    "iso_code": country.iso_code if country else "",
                    "safety_level": country.safety_level if country else "unknown",
                },
                "currency": currency,
                "airports": [{"name": a.name, "iata": a.iata_code} for a in airports],
                "rail_stations": [{"name": r.name, "code": r.station_code, "high_speed": r.is_high_speed} for r in rail],
                "recommended_hotels": [
                    {"name": h.name, "stars": h.star_rating, "tier": h.price_tier, "amenities": h.amenities}
                    for h in hotels
                ],
                "top_attractions": [{"name": a.name, "type": a.attraction_type, "tags": a.tags} for a in attractions],
                "museums": [{"name": m.name, "category": m.category} for m in museums],
                "restaurants": [{"name": r.name, "tier": r.price_tier} for r in restaurants],
                "football_clubs": [{"name": c.name, "league": c.league} for c in clubs],
                "sports_venues": [{"name": v.name, "type": v.venue_type, "capacity": v.capacity} for v in venues],
                "events": [{"name": e.name, "type": e.event_type, "month": e.month} for e in events],
                "local_transport": [{"name": t.name, "type": t.transport_type} for t in transport],
                "weather_overview": weather,
            },
            assumptions=["Hotel recommendations filtered by budget_style when profile provided"],
            limitations=["Sprint 1 graph covers 11 cities; others return not-found"],
        )

    # ------------------------------------------------------------------

    def _connected(self, node_id: str, entity_type: str, rel: RelationshipType, direction: str) -> list[Any]:
        return self._ks.get_connected_entities(node_id, entity_type, rel, direction)

    def _hotels(self, city_id: str, profile: dict | None) -> list[Any]:
        tier_map = {
            "backpacker": "budget", "budget": "budget",
            "balanced": "mid-range", "comfort": "luxury", "luxury": "luxury",
        }
        pref_tier = tier_map.get(
            (profile or {}).get("preferences", {}).get("budget_style", "balanced"), "mid-range"
        )
        hotels = self._connected(city_id, "Hotel", RelationshipType.LOCATED_IN, "inbound")
        match = [h for h in hotels if h.price_tier == pref_tier]
        return (match or hotels)[:3]

    def _weather(self, city_id: str) -> list[dict]:
        weather = self._ks.get_connected_entities(city_id, "Weather", RelationshipType.HAS_WEATHER, "outbound")
        return sorted(
            [{"month": w.month, "avg_temp_c": w.avg_temp_c, "condition": w.condition, "season": w.season} for w in weather],
            key=lambda x: x["month"],
        )

    def _currency(self, country: Any) -> dict | None:
        if country is None:
            return None
        currencies = self._ks.get_connected_entities(country.id, "Currency", RelationshipType.USES_CURRENCY, "outbound")
        if currencies:
            c = currencies[0]
            return {"code": c.code, "name": c.name, "symbol": c.symbol}
        return None

    def _region(self, city: Any) -> dict | None:
        regions = self._ks.get_connected_entities(city.id, "Region", RelationshipType.IN_REGION, "outbound")
        if regions:
            r = regions[0]
            return {"name": r.name, "type": r.region_type}
        return None


destination_reasoner = DestinationReasoner()
