"""UnifiedRecommendation — Trip Brain's single output shape."""

from __future__ import annotations

from dataclasses import dataclass, field

from ai.shared.agent_result import AgentResult


@dataclass
class UnifiedRecommendation:
    results: list[AgentResult] = field(default_factory=list)
    modules_selected: list[str] = field(default_factory=list)
    modules_succeeded: list[str] = field(default_factory=list)
    modules_failed: list[str] = field(default_factory=list)
    overall_confidence: float = 0.0
    synthesis_note: str = ""
