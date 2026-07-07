from typing import Type

from ai.agents.base_agent import BaseAgent


class AgentRegistry:
    """
    Central registry mapping agent names to their classes.

    New agents self-register; the Orchestrator never imports them directly.
    This decouples agent discovery from routing logic and makes the registry
    testable in isolation.
    """

    def __init__(self) -> None:
        self._registry: dict[str, Type[BaseAgent]] = {}

    def register(self, name: str, agent_class: Type[BaseAgent]) -> None:
        self._registry[name] = agent_class

    def get(self, name: str) -> Type[BaseAgent] | None:
        return self._registry.get(name)

    def is_registered(self, name: str) -> bool:
        return name in self._registry

    def list_agents(self) -> list[str]:
        return sorted(self._registry.keys())


def _build_default_registry() -> AgentRegistry:
    from ai.agents.travel_concierge_agent import TravelConciergeAgent
    from ai.agents.travel_manager_agent import TravelManagerAgent

    registry = AgentRegistry()
    registry.register("travel_concierge", TravelConciergeAgent)
    registry.register("travel_manager", TravelManagerAgent)
    return registry


default_registry = _build_default_registry()
