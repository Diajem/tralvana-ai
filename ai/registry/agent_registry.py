from typing import Any, Type


class AgentRegistry:
    """
    Central registry mapping agent names to specialist agent classes.

    The TravelManager routes all agent work through this registry.
    New specialist agents are registered here — never hardcoded into TravelManager.
    """

    def __init__(self) -> None:
        self._registry: dict[str, Type[Any]] = {}

    def register(self, name: str, agent_class: Type[Any]) -> None:
        self._registry[name] = agent_class

    def get(self, name: str) -> Type[Any] | None:
        return self._registry.get(name)

    def is_registered(self, name: str) -> bool:
        return name in self._registry

    def list_agents(self) -> list[str]:
        return sorted(self._registry.keys())


def _build_default_registry() -> AgentRegistry:
    from ai.agents.budget_agent import BudgetAgent
    from ai.agents.experience_agent import ExperienceAgent
    from ai.agents.flight_agent import FlightAgent
    from ai.agents.hotel_agent import HotelAgent
    from ai.agents.visa_agent import VisaAgent

    registry = AgentRegistry()
    registry.register("budget_agent", BudgetAgent)
    registry.register("experience_agent", ExperienceAgent)
    registry.register("flight_agent", FlightAgent)
    registry.register("hotel_agent", HotelAgent)
    registry.register("visa_agent", VisaAgent)
    return registry


default_registry = _build_default_registry()
