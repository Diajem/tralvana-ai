from __future__ import annotations

from typing import TYPE_CHECKING, Any

from knowledge.graph.relationships import RelationshipType

if TYPE_CHECKING:
    from knowledge.graph.knowledge_graph import KnowledgeGraph

_MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

_CONDITION_APPEAL: dict[str, int] = {
    "sunny": 5, "mild": 4, "partly-cloudy": 3,
    "hot": 3, "humid": 2, "cloudy": 2,
    "rainy": 1, "cold": 1, "snowy": 2,
}


class TimelineReasoner:
    """
    Advises on when to visit a destination and what to expect on a given date.

    Sprint 1: derives best travel months from weather and event data.
    Sprint 3+: incorporate flight price seasonality and crowd data.
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
        travel_month: int | None = None,
        duration_days: int = 7,
        traveller_profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        city = self._graph.find_node_by_name("City", destination)
        if city is None:
            return self._unknown(destination)

        weather_records = self._weather_for(city.id)
        events = self._events_for(city.id)
        best_months = self._best_months(weather_records, events)

        specific = None
        if travel_month is not None:
            specific = self._month_snapshot(travel_month, weather_records, events)

        interests = (traveller_profile or {}).get("preferences", {}).get("travel_interests", [])
        avoidance = self._seasonal_avoidance(weather_records, interests)

        return {
            "destination_found": True,
            "destination": destination,
            "best_months": best_months,
            "months_to_avoid": avoidance,
            "travel_month_snapshot": specific,
            "events_calendar": sorted(events, key=lambda e: e.get("month") or 0),
            "planning_tips": self._planning_tips(destination, duration_days),
            "confidence": 0.7,
            "reasoning_source": "knowledge_graph_v1_weather_events",
        }

    # ------------------------------------------------------------------

    def _weather_for(self, city_id: str) -> list[Any]:
        edges = self._graph.get_outbound_edges(city_id, RelationshipType.HAS_WEATHER)
        records = []
        for e in edges:
            node = self._graph.get_node(e.target_id)
            if node:
                records.append(node)
        return sorted(records, key=lambda w: w.month)

    def _events_for(self, city_id: str) -> list[dict]:
        edges = self._graph.get_inbound_edges(city_id, RelationshipType.PART_OF)
        results = []
        for e in edges:
            node = self._graph.get_node(e.source_id)
            if node and self._graph.get_node_type(e.source_id) == "Event":
                results.append({
                    "name": node.name,
                    "type": node.event_type,
                    "month": node.month,
                    "month_name": _MONTH_NAMES[node.month] if node.month else "Unknown",
                })
        return results

    def _best_months(self, weather_records: list, events: list[dict]) -> list[dict]:
        event_months: set[int] = {e["month"] for e in events if e["month"]}
        scored: list[tuple[int, int]] = []

        for w in weather_records:
            score = _CONDITION_APPEAL.get(w.condition, 2)
            if w.month in event_months:
                score += 1
            scored.append((w.month, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = [
            {
                "month": m,
                "month_name": _MONTH_NAMES[m],
                "weather_score": s,
                "has_events": m in event_months,
            }
            for m, s in scored[:3]
        ]
        return top

    def _month_snapshot(
        self,
        month: int,
        weather_records: list,
        events: list[dict],
    ) -> dict:
        weather = next((w for w in weather_records if w.month == month), None)
        month_events = [e for e in events if e.get("month") == month]

        return {
            "month": month,
            "month_name": _MONTH_NAMES[month],
            "weather": {
                "avg_temp_c": weather.avg_temp_c if weather else None,
                "condition": weather.condition if weather else "no data",
                "season": weather.season if weather else "unknown",
            },
            "events_this_month": month_events,
            "travel_advice": self._advice_for_weather(weather),
        }

    def _advice_for_weather(self, weather: Any) -> str:
        if weather is None:
            return "No weather data available for this month."
        t = weather.avg_temp_c
        condition = weather.condition
        if condition in ("hot", "humid") and t > 35:
            return "Very hot — pack light breathable clothing and stay hydrated."
        if condition in ("rainy",):
            return "Rainy season — bring waterproofs and expect some indoor days."
        if condition in ("cold", "snowy") and t < 5:
            return "Cold — pack warm layers and check for winter closures."
        if condition in ("sunny", "mild"):
            return "Excellent conditions — ideal for sightseeing and outdoor activities."
        return "Comfortable conditions — standard packing applies."

    def _seasonal_avoidance(self, weather_records: list, interests: list[str]) -> list[dict]:
        avoid = []
        for w in weather_records:
            if w.condition == "rainy" and "nature" in interests:
                avoid.append({
                    "month": w.month,
                    "month_name": _MONTH_NAMES[w.month],
                    "reason": "Rainy season limits outdoor activities.",
                })
            elif w.condition in ("hot",) and w.avg_temp_c > 38:
                avoid.append({
                    "month": w.month,
                    "month_name": _MONTH_NAMES[w.month],
                    "reason": f"Extreme heat ({w.avg_temp_c}°C) — uncomfortable for most travellers.",
                })
        return avoid

    def _planning_tips(self, destination: str, duration_days: int) -> list[str]:
        tips = [
            f"Book accommodation at least 6 weeks in advance for {destination}.",
            f"A {duration_days}-day trip allows time for 2–3 day trips outside the city centre.",
            "Check visa requirements well in advance — processing can take 4–8 weeks.",
            "Purchase travel insurance before departure.",
        ]
        return tips

    def _unknown(self, destination: str) -> dict[str, Any]:
        return {
            "destination_found": False,
            "destination_queried": destination,
            "message": f"'{destination}' is not yet in the TravelOS Knowledge Graph.",
            "reasoning_source": "knowledge_graph_v1_weather_events",
        }


timeline_reasoner = TimelineReasoner()
