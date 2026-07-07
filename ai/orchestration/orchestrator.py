import uuid
from typing import Any

from ai.agents.base_agent import AgentContext, AgentResult
from ai.orchestration.agent_registry import AgentRegistry, default_registry


class Orchestrator:
    """
    Routes incoming requests to the appropriate agent via the AgentRegistry.
    Manages session context for each run.
    """

    def __init__(self, registry: AgentRegistry | None = None) -> None:
        self._registry = registry or default_registry

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
        agent_class = self._registry.get(agent_name)
        if agent_class is None:
            return AgentResult(
                success=False,
                output=None,
                error=f"Unknown agent: '{agent_name}'. Available: {self._registry.list_agents()}",
            )

        context = self.new_context(traveller_id)

        if traveller_id:
            from ai.memory.traveller_intelligence_service import traveller_intelligence_service
            context.traveller_profile = traveller_intelligence_service.build_context_data(traveller_id)

        agent = agent_class(context)
        return await agent.run(input_data)

    def list_agents(self) -> list[str]:
        return self._registry.list_agents()


default_orchestrator = Orchestrator()
