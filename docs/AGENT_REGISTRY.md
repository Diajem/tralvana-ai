# Agent Registry — Specification

## Overview

The Agent Registry maps agent names (strings) to agent classes (Python types).
It decouples the Orchestrator from any specific agent implementation —
the Orchestrator never imports agent classes directly.

**File:** `ai/orchestration/agent_registry.py`

---

## Design

```python
class AgentRegistry:
    def register(self, name: str, agent_class: Type[BaseAgent]) -> None
    def get(self, name: str) -> Type[BaseAgent] | None
    def is_registered(self, name: str) -> bool
    def list_agents(self) -> list[str]
```

A module-level `default_registry` singleton is pre-populated with all built-in agents.
New agents are registered in `_build_default_registry()`.

---

## Registered Agents (Sprint 1)

| Name | Class | Entry point |
|------|-------|-------------|
| `travel_concierge` | `TravelConciergeAgent` | Primary conversation entry point |
| `travel_manager` | `TravelManagerAgent` | Trip planning coordinator |

---

## How the Orchestrator Uses the Registry

```python
class Orchestrator:
    def __init__(self, registry: AgentRegistry | None = None) -> None:
        self._registry = registry or default_registry

    async def run(self, agent_name: str, input_data: dict, ...) -> AgentResult:
        agent_class = self._registry.get(agent_name)
        if agent_class is None:
            return AgentResult(
                success=False,
                output=None,
                error=f"Unknown agent: {agent_name}. Available: {self._registry.list_agents()}",
            )
        context = self.new_context(traveller_id)
        agent = agent_class(context)
        return await agent.run(input_data)
```

The Orchestrator exposes a `default_orchestrator` module-level singleton.

---

## Adding a New Agent

1. Create your agent class in `ai/agents/`:

```python
class DestinationResearchAgent(BaseAgent):
    name = "destination_research"
    description = "Researches destination details and travel conditions."

    async def run(self, input_data: dict[str, Any]) -> AgentResult:
        ...
```

2. Register it in `_build_default_registry()`:

```python
def _build_default_registry() -> AgentRegistry:
    from ai.agents.travel_concierge_agent import TravelConciergeAgent
    from ai.agents.travel_manager_agent import TravelManagerAgent
    from ai.agents.destination_research_agent import DestinationResearchAgent

    registry = AgentRegistry()
    registry.register("travel_concierge", TravelConciergeAgent)
    registry.register("travel_manager", TravelManagerAgent)
    registry.register("destination_research", DestinationResearchAgent)
    return registry
```

3. Dispatch to it from any existing agent or the ConversationEngine:

```python
result = await default_orchestrator.run("destination_research", {"destination": "Lagos"})
```

---

## Routing Table

| Task Type | Agent Name | Sprint |
|-----------|-----------|--------|
| Conversation entry | `travel_concierge` | 1 |
| Trip planning | `travel_manager` | 1 |
| Destination research | `destination_research` | 4 |
| Flight search | `flight_search` | 4 |
| Hotel search | `hotel_search` | 4 |
| Budget estimation | `budget_estimator` | 4 |
| Itinerary generation | `itinerary_builder` | 4 |
| Weather lookup | `weather_advisor` | 5 |
| Visa check | `visa_advisor` | 5 |

---

## 3-Tier Model Routing

Future versions of the registry will carry a `model_tier` annotation per agent:

| Tier | Model | Use cases |
|------|-------|-----------|
| 1 | Direct transform (no LLM) | Simple lookups, format conversions |
| 2 | Haiku | Classification, extraction, short answers |
| 3 | Sonnet / Opus | Reasoning, planning, multi-step tasks |

The Orchestrator will select the model tier at dispatch time based on the agent's annotation.

---

## Sprint 1 Constraints

- Registry is populated once at module load (`_build_default_registry()`).
- No hot-reload, no persistence.
- Agents are stateless — new instance created per `Orchestrator.run()` call.
- Model-tier routing is not yet implemented.
