"""UnifiedRecommendation — Trip Brain's single output shape."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ai.shared.agent_result import AgentResult


@dataclass
class UnifiedRecommendation:
    results: list[AgentResult] = field(default_factory=list)
    modules_selected: list[str] = field(default_factory=list)
    modules_succeeded: list[str] = field(default_factory=list)
    modules_failed: list[str] = field(default_factory=list)
    overall_confidence: float = 0.0
    synthesis_note: str = ""
    # Presentation conflicts detected by ai/trip_brain/conflicts.py — kept
    # here (not just as a side-effect note on one module's assumptions) so
    # the Explainability Engine can surface them as trade-offs without
    # re-deriving them (docs/EXPLAINABILITY_ENGINE.md).
    conflicts: list[str] = field(default_factory=list)
    # The Explainability Engine's structured output, computed once per
    # plan() call, right after conflict resolution and confidence
    # aggregation (docs/EXPLAINABILITY_ENGINE.md's Trip Brain Integration
    # section) — never recomputed by a caller that already has a
    # UnifiedRecommendation in hand.
    explanation: dict[str, Any] = field(default_factory=dict)
    # Kept alongside `explanation` so a caller re-deriving only the
    # question-sensitive summary line (services/api/app/routers/explain.py)
    # doesn't lose destination context that was already known at plan()
    # time.
    destination: str = ""
