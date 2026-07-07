from typing import Any

from ai.memory.memory_service import MemoryService, memory_service


class TravellerIntelligenceService:
    """
    Enriches raw TIP data for agent consumption.
    Adds derived intelligence (travel style, preference summary) on top of
    the stored profile so agents receive structured, actionable context.
    """

    def __init__(self, mem: MemoryService) -> None:
        self._mem = mem

    def build_context_data(self, traveller_id: str) -> dict[str, Any] | None:
        """Returns an enriched profile dict for injection into AgentContext."""
        profile = self._mem.retrieve_profile(traveller_id)
        if not profile:
            return None
        return {
            **profile,
            "intelligence": {
                "travel_style": self._infer_travel_style(profile),
                "preference_summary": self._preference_summary(profile),
            },
        }

    def store_profile(self, traveller_id: str, profile: dict[str, Any]) -> None:
        """Forwards profile storage to the underlying MemoryService."""
        self._mem.store_profile(traveller_id, profile)

    def _infer_travel_style(self, profile: dict[str, Any]) -> str:
        prefs = profile.get("preferences", {})
        cabin = prefs.get("cabin_class", "economy")
        budget = prefs.get("budget_style", "balanced")
        interests = prefs.get("travel_interests", [])

        if cabin == "first" or budget == "luxury":
            return "luxury traveller"
        if cabin == "business" or budget == "comfort":
            return "business traveller" if "business" in interests else "comfort traveller"
        if budget in ("backpacker", "budget"):
            return "budget traveller"
        if "adventure" in interests or "nature" in interests:
            return "adventure traveller"
        return "leisure traveller"

    def _preference_summary(self, profile: dict[str, Any]) -> dict[str, Any]:
        prefs = profile.get("preferences", {})
        identity = profile.get("identity", {})
        return {
            "name": identity.get("name", ""),
            "home_airport": prefs.get("home_airport", ""),
            "currency": prefs.get("preferred_currency", "USD"),
            "language": prefs.get("preferred_language", "en"),
            "budget_style": prefs.get("budget_style", "balanced"),
            "cabin_class": prefs.get("cabin_class", "economy"),
            "seat": prefs.get("seat", "no_preference"),
            "meal": prefs.get("meal", "standard"),
            "accommodation": prefs.get("accommodation_type", "hotel"),
            "interests": prefs.get("travel_interests", []),
            "hotel_preferences": prefs.get("hotel_preferences", []),
            "accessibility": prefs.get("accessibility_needs", []),
        }


# Module-level singleton — shares the MemoryService instance
traveller_intelligence_service = TravellerIntelligenceService(memory_service)
