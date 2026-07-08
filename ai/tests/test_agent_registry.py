import pytest

from ai.registry.agent_registry import AgentRegistry, default_registry


class TestAgentRegistry:
    def test_default_registry_has_agents(self):
        agents = default_registry.list_agents()
        assert len(agents) > 0

    def test_flight_agent_registered(self):
        assert default_registry.is_registered("flight_agent")

    def test_budget_agent_registered(self):
        assert default_registry.is_registered("budget_agent")

    def test_get_known_agent_returns_class(self):
        agent_class = default_registry.get("flight_agent")
        assert agent_class is not None

    def test_get_unknown_agent_returns_none(self):
        agent_class = default_registry.get("nonexistent_agent")
        assert agent_class is None

    def test_is_registered_true_for_known(self):
        assert default_registry.is_registered("flight_agent") is True

    def test_is_registered_false_for_unknown(self):
        assert default_registry.is_registered("ghost_agent") is False

    def test_list_agents_is_sorted(self):
        agents = default_registry.list_agents()
        assert agents == sorted(agents)

    def test_custom_registry_register_and_get(self):
        registry = AgentRegistry()

        class FakeAgent:
            pass

        registry.register("fake_agent", FakeAgent)
        assert registry.get("fake_agent") is FakeAgent
        assert registry.is_registered("fake_agent")

    def test_custom_registry_empty_by_default(self):
        registry = AgentRegistry()
        assert registry.list_agents() == []
