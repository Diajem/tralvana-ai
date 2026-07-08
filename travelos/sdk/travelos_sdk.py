from __future__ import annotations

from typing import Any

from travelos.registry.service_registry import ServiceRegistry, service_registry as _default_registry


class TravelOS:
    """
    Public SDK for TravelOS.

    Provides a single, stable entry point to all TravelOS capabilities.
    Internal services, repositories, and AI modules are implementation
    details â€” nothing outside this SDK should import them directly.

    Usage (sync):
        from travelos.sdk.travelos_sdk import travelos

        traveller = travelos.createTraveller({...})
        goal      = travelos.createGoal({...})
        trip      = travelos.planTrip({...})
        results   = travelos.searchKnowledge("Tokyo", entity_type="City")

    Usage (async â€” conversation and reasoning):
        reply = await travelos.chat("I want to visit Japan in October")
    """

    def __init__(self, registry: ServiceRegistry | None = None) -> None:
        self._registry = registry or _default_registry

    # ------------------------------------------------------------------
    # Traveller
    # ------------------------------------------------------------------

    def createTraveller(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new traveller profile.

        `data` must match CreateProfileRequest (identity, preferences, loyalty).
        Returns the created profile dict.
        """
        from app.models.traveller import CreateProfileRequest
        svc = self._registry.get("traveller_service")
        request = CreateProfileRequest(**data)
        return svc.create_profile(request)

    def getTraveller(self, traveller_id: str) -> dict[str, Any] | None:
        """Return a traveller profile by ID, or None if not found."""
        svc = self._registry.get("traveller_service")
        return svc.get_profile(traveller_id)

    # ------------------------------------------------------------------
    # Goals
    # ------------------------------------------------------------------

    def createGoal(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a travel goal.

        `data` must match CreateGoalRequest fields.
        Returns the created goal dict.
        """
        from app.domains.goals.schemas import CreateGoalRequest
        svc = self._registry.get("goal_service")
        request = CreateGoalRequest(**data)
        return svc.create(request)

    def getGoal(self, goal_id: str) -> dict[str, Any] | None:
        """Return a goal by ID, or None if not found."""
        svc = self._registry.get("goal_service")
        return svc.get(goal_id)

    # ------------------------------------------------------------------
    # Trip Planning
    # ------------------------------------------------------------------

    def planTrip(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Generate a full trip plan.

        `data` must match CreateTripPlanRequest fields.
        Returns the planned trip dict (itinerary, budget, risks, confidence).
        """
        from app.domains.trips.schemas import CreateTripPlanRequest
        svc = self._registry.get("trip_planning_service")
        request = CreateTripPlanRequest(**data)
        return svc.plan(request)

    # ------------------------------------------------------------------
    # Conversation
    # ------------------------------------------------------------------

    async def chat(
        self,
        message: str,
        traveller_id: str | None = None,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Send a message to the TravelOS AI concierge.

        Returns a structured response with intent, reply, confidence,
        and optionally goal_id and trip_id if the engine creates them.
        """
        from ai.concierge.travel_concierge import travel_concierge
        return await travel_concierge.handle(
            message,
            traveller_id=traveller_id,
            conversation_id=conversation_id,
        )

    # ------------------------------------------------------------------
    # Reasoning
    # ------------------------------------------------------------------

    def reason(self, goal_id: str) -> dict[str, Any]:
        """
        Run the goal reasoner against an existing goal.

        Returns planning_readiness_score, missing_information,
        suitable_agents, and next_steps.
        """
        from ai.goals.goal_reasoner import GoalReasoner
        goal_svc = self._registry.get("goal_service")
        goal = goal_svc.get(goal_id)
        if not goal:
            return {"error": f"Goal '{goal_id}' not found", "success": False}
        reasoner = GoalReasoner()
        result = reasoner.reason(goal)
        return {"success": True, "goal_id": goal_id, **result}

    # ------------------------------------------------------------------
    # Knowledge
    # ------------------------------------------------------------------

    def searchKnowledge(
        self,
        query: str,
        entity_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search the Knowledge Graph by name fragment.

        If entity_type is provided, narrows the search to that type
        (e.g. "City", "Airport", "FootballClub").
        Returns a list of matching entities as dicts.
        """
        svc = self._registry.get("knowledge_service")
        if entity_type:
            raw = svc.search_entities(entity_type, query)
        else:
            # Search across all well-known entity types
            raw = []
            for etype in ("City", "Airport", "Attraction", "Restaurant",
                          "FootballClub", "Event", "Transport"):
                raw.extend(svc.search_entities(etype, query))
        # Entities may be dataclasses or dicts â€” normalise to dict
        result = []
        for entity in raw:
            if hasattr(entity, "__dict__"):
                result.append(vars(entity))
            elif isinstance(entity, dict):
                result.append(entity)
        return result

    def getKnowledge(
        self,
        entity_type: str,
        name: str,
    ) -> dict[str, Any] | None:
        """
        Retrieve a single entity from the Knowledge Graph by exact name.

        Example: travelos.getKnowledge("City", "Tokyo")
        Returns the entity as a dict, or None if not found.
        """
        svc = self._registry.get("knowledge_service")
        entity = svc.find_entity(entity_type, name)
        if entity is None:
            return None
        if hasattr(entity, "__dict__"):
            return vars(entity)
        if isinstance(entity, dict):
            return entity
        return {"value": entity}


travelos = TravelOS()
