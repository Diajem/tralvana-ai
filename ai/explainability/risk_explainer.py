"""
Risk Explainer — preserves every module's own risk text verbatim, and
makes partial module failure visible as a risk in its own right
(docs/TRIP_BRAIN_ARCHITECTURE.md's Failure Handling: "Graceful
degradation, not failure" — the gap must still be named, not hidden).

A FAILED module's own `.risks` (an internal exception message) is not
surfaced verbatim to the traveller — a plain-language note that the
module could not be completed replaces it. No risk text is invented for
a module that succeeded; only what that module already reported.
"""

from __future__ import annotations

from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus


def collect(results: list[AgentResult], modules_failed: list[str] | None = None) -> list[str]:
    seen: list[str] = []
    for result in results:
        if result.status == AgentStatus.FAILED:
            continue
        for risk in result.risks:
            if risk not in seen:
                seen.append(risk)

    for name in modules_failed or []:
        note = f"{name} could not be completed — that part of the recommendation is missing."
        if note not in seen:
            seen.append(note)

    return seen
