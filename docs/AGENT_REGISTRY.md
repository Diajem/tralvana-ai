# Agent Registry — Specification

## Overview

The Agent Registry maps agent names (strings) to specialist agent classes (Python types).
It decouples the TravelManager from any specific agent implementation.

The TravelManager never imports agent classes directly. It only queries the registry.

**File:** `ai/registry/agent_registry.py`

---

## API

```python
class AgentRegistry:
    def register(self, name: str, agent_class: Type) -> None
    def get(self, name: str) -> Type | None
    def is_registered(self, name: str) -> bool
    def list_agents(self) -> list[str]
```

A module-level `default_registry` singleton is pre-populated with all built-in agents.

---

## Registered Agents (Sprint 1)

| Name | Class | Responsibility |
|------|-------|---------------|
| `budget_agent` | `BudgetAgent` | Estimate travel costs using traveller's budget style |
| `experience_agent` | `ExperienceAgent` | Provide destination highlights and local tips |
| `flight_agent` | `FlightAgent` | Search and recommend flights |
| `hotel_agent` | `HotelAgent` | Search and recommend accommodation |
| `visa_agent` | `VisaAgent` | Check visa requirements for the destination |

---

## How TravelManager Uses the Registry

```python
class TravelManager:
    def __init__(self, registry: AgentRegistry | None = None) -> None:
        self._registry = registry or default_registry

    async def execute(self, ...) -> list[AgentResult]:
        for agent_name in decision.requires_agents:
            agent_class = self._registry.get(agent_name)
            if agent_class is None:
                continue
            agent = agent_class(context)
            tasks.append(agent.run(input_data))

        raw = await asyncio.gather(*tasks, return_exceptions=True)
        ...
```

Agents run concurrently. One failure does not block the rest.

---

## AgentResult Contract

Every agent must return an `AgentResult` (from `ai/shared/agent_result.py`):

```python
@dataclass
class AgentResult:
    agent_name: str
    status: AgentStatus       # SUCCESS | NEEDS_INFORMATION | FAILED | PARTIAL | SKIPPED
    confidence: float         # 0.0 – 1.0
    data: dict
    assumptions: list[str]
    missing_information: list[str]
    risks: list[str]
    recommendations: list[str]
    next_actions: list[str]
```

---

## Adding a New Specialist Agent

**Step 1 — Create the agent class in `ai/agents/`:**

```python
# ai/agents/weather_agent.py
from ai.shared.agent_context import AgentContext
from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus

class WeatherAgent:
    name = "weather_agent"

    def __init__(self, context: AgentContext) -> None:
        self.context = context

    async def run(self, input_data: dict) -> AgentResult:
        destination = input_data.get("destination", "")
        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.SUCCESS,
            confidence=0.6,
            data={"destination": destination, "forecast": "pending_live_data"},
            assumptions=["Live weather data activates in Sprint 5."],
            recommendations=["Pack for varied conditions."],
        )
```

**Step 2 — Register it in `_build_default_registry()`:**

```python
def _build_default_registry() -> AgentRegistry:
    ...
    from ai.agents.weather_agent import WeatherAgent
    registry.register("weather_agent", WeatherAgent)
    return registry
```

**Step 3 — Add it to the DecisionEngine dispatch map (`_AGENT_MAP`) if needed:**

```python
_AGENT_MAP: dict[Intent, list[str]] = {
    Intent.DESTINATION_QUESTION: ["experience_agent", "weather_agent"],
    ...
}
```

No other files change.

---

## Full Agent Routing Table

| Intent | Agents (Sprint 1) | Future Agents |
|--------|------------------|--------------|
| `PLAN_TRIP` | flight, hotel, budget, experience, visa | weather, itinerary, insurance |
| `MODIFY_TRIP` | flight, hotel | rebooking |
| `DESTINATION_QUESTION` | experience | weather, safety |
| `TRAVEL_ADVICE` | experience | curated-content |
| `BUDGET_ADVICE` | budget | currency, deals |
| `VIEW_PROFILE` | (none) | — |
| `UPDATE_PREFERENCES` | (none) | — |
| `GENERAL_CONVERSATION` | (none) | — |

---

## Sprint 1 Constraints

- Registry populated once at module load — no hot-reload.
- Agents are stateless — new instance created per `TravelManager.execute()` call.
- Model-tier routing (Haiku / Sonnet / Opus) deferred to Sprint 3.
