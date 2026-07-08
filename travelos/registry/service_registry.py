from __future__ import annotations

import importlib
from typing import Any

from travelos.logging.travel_logger import TravelLogger

_logger = TravelLogger.for_service("ServiceRegistry")

# Canonical names and their module + attribute paths.
# Paths use `app.*` because services run with services/api/ in sys.path.
_SERVICE_MAP: dict[str, tuple[str, str]] = {
    "traveller_service": ("app.services.traveller_service", "traveller_service"),
    "goal_service": ("app.domains.goals.service", "goal_service"),
    "conversation_engine": ("ai.concierge.conversation_engine", "conversation_engine"),
    "knowledge_service": ("ai.intelligence.knowledge.knowledge_service", "knowledge_service"),
    "trip_planning_service": ("app.domains.trips.service", "trip_planning_service"),
    "memory_service": ("ai.memory.traveller_intelligence_service", "traveller_intelligence_service"),
    "travel_manager": ("ai.manager.travel_manager", "travel_manager"),
}


class ServiceRegistry:
    """
    Discovers and provides access to all TravelOS services.

    Services are resolved lazily on first access.  A service can be
    overridden at runtime (e.g. for testing) via `register()`.

    Known services:
        traveller_service      â€” TravellerService singleton
        goal_service           â€” GoalService singleton
        conversation_engine    â€” ConversationEngine (ai/concierge)
        knowledge_service      â€” KnowledgeService singleton
        trip_planning_service  â€” TripPlanningService singleton
        memory_service         â€” TravellerIntelligenceService singleton
        travel_manager         â€” TravelManager singleton
    """

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def get(self, name: str) -> Any:
        """
        Resolve a service by name.

        Raises KeyError for unknown names.
        Raises RuntimeError if the service module cannot be imported.
        """
        if name in self._cache:
            return self._cache[name]

        if name not in _SERVICE_MAP:
            raise KeyError(
                f"Unknown service: '{name}'. "
                f"Known services: {self.available()}"
            )

        module_path, attr = _SERVICE_MAP[name]
        service = self._load(name, module_path, attr)
        self._cache[name] = service
        _logger.debug("Service resolved", service=name, module=module_path)
        return service

    def _load(self, name: str, module_path: str, attr: str) -> Any:
        try:
            mod = importlib.import_module(module_path)
            return getattr(mod, attr)
        except ImportError as exc:
            raise RuntimeError(
                f"Cannot import service '{name}' from '{module_path}': {exc}"
            ) from exc
        except AttributeError as exc:
            raise RuntimeError(
                f"Module '{module_path}' has no attribute '{attr}': {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Registration (override or extend)
    # ------------------------------------------------------------------

    def register(self, name: str, service: Any) -> None:
        """Register or override a service instance (useful for testing)."""
        self._cache[name] = service
        _logger.debug("Service registered manually", service=name)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def available(self) -> list[str]:
        return sorted(_SERVICE_MAP.keys())

    def loaded(self) -> list[str]:
        return sorted(self._cache.keys())

    def is_known(self, name: str) -> bool:
        return name in _SERVICE_MAP or name in self._cache

    def reset(self) -> None:
        """Clear resolved cache. Used in tests."""
        self._cache.clear()


service_registry = ServiceRegistry()
