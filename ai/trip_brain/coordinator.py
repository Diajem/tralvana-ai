"""
Trip Brain — the Coordinator (docs/ORCHESTRATION_PATTERN.md, "Coordinator"
section; docs/TRIP_BRAIN_ARCHITECTURE.md for the full lifecycle).

Given the Planner's output (Intent + entities, already produced by
IntentClassifier + DecisionEngine, unchanged) plus assembled context,
decides which Discovery modules are relevant, runs them, merges their
results, resolves presentation conflicts between them, and produces one
UnifiedRecommendation.

Trip Brain is an orchestration layer, not a seventh Discovery module — it
has no scoring, ranking, or domain reasoning of its own. Every module call
goes through ai/trip_brain/discovery_adapters.py, which calls exactly the
same public service.recommend()/check()/analyse() entrypoint
ConversationEngine already calls for narrow intents.
"""

from __future__ import annotations

import asyncio
from typing import Any

from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus
from ai.trip_brain.confidence import aggregate_confidence
from ai.trip_brain.conflicts import detect_conflicts
from ai.trip_brain.context import ContextBuilder, TripBrainContext
from ai.trip_brain.discovery_adapters import MODULE_RUNNERS
from ai.trip_brain.models import UnifiedRecommendation
from ai.trip_brain.module_selection import ALL_MODULES, ModuleSelector
from ai.trip_brain.synthesis import build_synthesis_note


class TripBrain:
    def __init__(
        self,
        context_builder: ContextBuilder | None = None,
        selector: ModuleSelector | None = None,
    ) -> None:
        self._context_builder = context_builder or ContextBuilder()
        self._selector = selector or ModuleSelector()

    async def plan(
        self,
        traveller_id: str | None,
        trip_id: str | None,
        goal_id: str | None,
        entities: dict[str, str],
        profile: dict[str, Any] | None,
    ) -> UnifiedRecommendation:
        context = self._context_builder.build(
            traveller_id, trip_id, goal_id, entities, profile
        )
        weights = self._selector.select(context)

        if not weights:
            return UnifiedRecommendation()

        module_results = await self._run_modules(context, weights)

        modules_succeeded = [
            name for name in weights if module_results[name].status != AgentStatus.FAILED
        ]
        modules_failed = [
            name for name in weights if module_results[name].status == AgentStatus.FAILED
        ]

        detect_conflicts(module_results)

        overall_confidence = aggregate_confidence(
            {name: module_results[name].confidence for name in weights},
            weights,
            modules_succeeded,
        )

        synthesis_note = build_synthesis_note(context.destination, modules_succeeded)

        ordered_results = [
            module_results[name] for name in ALL_MODULES if name in module_results
        ]

        return UnifiedRecommendation(
            results=ordered_results,
            modules_selected=list(weights.keys()),
            modules_succeeded=modules_succeeded,
            modules_failed=modules_failed,
            overall_confidence=overall_confidence,
            synthesis_note=synthesis_note,
        )

    async def _run_modules(
        self, context: TripBrainContext, weights: dict[str, float]
    ) -> dict[str, AgentResult]:
        async def run_one(name: str) -> tuple[str, AgentResult]:
            runner = MODULE_RUNNERS[name]
            agent_name = f"{name}_intelligence"
            try:
                result = await asyncio.to_thread(runner, context)
            except Exception as exc:  # belt-and-braces: adapters already isolate their own failures
                result = AgentResult(
                    agent_name=agent_name,
                    status=AgentStatus.FAILED,
                    confidence=0.0,
                    risks=[f"{agent_name} raised an exception: {exc}"],
                )
            return name, result

        pairs = await asyncio.gather(*(run_one(name) for name in weights))
        return dict(pairs)


trip_brain = TripBrain()
