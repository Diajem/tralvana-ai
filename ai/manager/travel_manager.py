import asyncio
from typing import Any

from ai.concierge.decision_engine import Decision
from ai.concierge.intent_classifier import Intent
from ai.registry.agent_registry import AgentRegistry, default_registry
from ai.shared.agent_context import AgentContext
from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus


class TravelManager:
    """
    Receives a Decision from DecisionEngine and dispatches work to specialist agents
    via the AgentRegistry.

    Agents run concurrently where possible. A failure in one agent does not
    block the others.

    The TravelManager does not know which agents exist — it only asks the registry.
    """

    def __init__(self, registry: AgentRegistry | None = None) -> None:
        self._registry = registry or default_registry

    async def execute(
        self,
        intent: Intent,
        context: AgentContext,
        decision: Decision,
        input_data: dict[str, Any],
    ) -> list[AgentResult]:
        if not decision.has_enough_information or not decision.requires_agents:
            return []

        tasks: list[Any] = []
        agent_names: list[str] = []

        for agent_name in decision.requires_agents:
            agent_class = self._registry.get(agent_name)
            if agent_class is None:
                continue
            agent = agent_class(context)
            tasks.append(agent.run(input_data))
            agent_names.append(agent_name)

        if not tasks:
            return []

        raw = await asyncio.gather(*tasks, return_exceptions=True)

        results: list[AgentResult] = []
        for name, outcome in zip(agent_names, raw):
            if isinstance(outcome, AgentResult):
                results.append(outcome)
            else:
                results.append(AgentResult(
                    agent_name=name,
                    status=AgentStatus.FAILED,
                    confidence=0.0,
                    risks=[f"Agent raised an exception: {outcome}"],
                ))

        return results

    def list_agents(self) -> list[str]:
        return self._registry.list_agents()


travel_manager = TravelManager()
