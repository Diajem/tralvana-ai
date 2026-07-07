import uuid
from typing import Any, Type

from ai.agents.base_agent import AgentContext, AgentResult, BaseAgent
from ai.agents.travel_manager_agent import TravelManagerAgent

AGENT_REGISTRY: dict[str, Type[BaseAgent]] = {
    "travel_manager": TravelManagerAgent,
}


class Orchestrator:
    """
    Routes incoming requests to the appropriate agent.
    Manages session context for each run.
    """

    def new_context(self, traveller_id: str | None = None) -> AgentContext:
        return AgentContext(
            session_id=str(uuid.uuid4()),
            traveller_id=traveller_id,
        )

    async def run(
        self,
        agent_name: str,
        input_data: dict[str, Any],
        traveller_id: str | None = None,
    ) -> AgentResult:
        agent_class = AGENT_REGISTRY.get(agent_name)
        if agent_class is None:
            from ai.agents.base_agent import AgentResult
            return AgentResult(
                success=False,
                output=None,
                error=f"Unknown agent: {agent_name}",
            )

        context = self.new_context(traveller_id)
        agent = agent_class(context)
        return await agent.run(input_data)

    def list_agents(self) -> list[str]:
        return list(AGENT_REGISTRY.keys())
