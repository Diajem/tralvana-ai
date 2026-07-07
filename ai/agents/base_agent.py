from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentContext:
    session_id: str
    traveller_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    success: bool
    output: Any
    error: str | None = None


class BaseAgent(ABC):
    """All Tralvana agents inherit from this class."""

    name: str = "base"
    description: str = ""

    def __init__(self, context: AgentContext):
        self.context = context

    @abstractmethod
    async def run(self, input_data: dict[str, Any]) -> AgentResult:
        """Execute the agent's primary task."""
        ...

    def _ok(self, output: Any) -> AgentResult:
        return AgentResult(success=True, output=output)

    def _err(self, message: str) -> AgentResult:
        return AgentResult(success=False, output=None, error=message)
