from dataclasses import dataclass, field
from typing import Any

from ai.shared.agent_status import AgentStatus


@dataclass
class AgentResult:
    agent_name: str
    status: AgentStatus
    confidence: float  # 0.0 – 1.0
    data: dict[str, Any] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "status": self.status.value,
            "confidence": self.confidence,
            "data": self.data,
            "assumptions": self.assumptions,
            "missing_information": self.missing_information,
            "risks": self.risks,
            "recommendations": self.recommendations,
            "next_actions": self.next_actions,
        }
