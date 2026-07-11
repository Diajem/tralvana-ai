# ADR-018: Legacy Orchestration Retirement — Investigation Outcome

**Date**: 2026-07-11
**Status**: Accepted
**Sprint**: 2 (T-023)

## Context

ADR-017 and `docs/TRIP_BRAIN_ARCHITECTURE.md` stated that T-022 would leave
`ai/manager/TravelManager`, `ai/registry/AgentRegistry`, and the five
placeholder agents (`ai/agents/{flight,hotel,budget,experience,visa}_agent.py`)
"in place, uncalled, as a rollback path," to be deleted wholesale by a later
T-023 once Trip Brain was verified. `docs/TASK_TRACKER.md`'s T-023 entry
matched this: "Removes `ai/manager/`, `ai/registry/`, and the five
placeholder agent files ... once T-022 has been fully implemented and
verified."

T-023 was scoped to retire this code, but with an explicit precondition
this ADR exists to record the result of: **"Retire only code proven to be
unused"** / **"Trace every import and runtime reference before deleting
anything"** / **"Remove only genuinely unused legacy orchestration files."**

## Investigation

A full-repository import and runtime-reference trace was run against
`ai/manager/`, `ai/registry/`, and the five agent files — every `.py` file
under `ai/`, `services/`, `apps/web/` searched for `TravelManager`,
`travel_manager`, `AgentRegistry`, `agent_registry`, `ai.manager`,
`ai.registry`, `ai.agents`, and each of the five agent class/module names.

**Finding: the premise was wrong.** `ai/concierge/conversation_engine.py`
(`ConversationEngine.process()`) has three live routing branches, not two:

1. Six narrow Discovery intents (`FLIGHT_SEARCH`, `ACCOMMODATION_SEARCH`,
   `DESTINATION_DISCOVERY`, `BUDGET_ANALYSIS`, `VISA_CHECK`,
   `WEATHER_ANALYSIS`) → call their Discovery module directly. Unaffected
   by T-022 or T-023.
2. `PLAN_TRIP` → routes through `ai/trip_brain/coordinator.py`
   (`trip_brain.plan()`), per T-022. Never touches `TravelManager`.
3. **Everything else that needs agents** — `elif decision.has_enough_information
   and decision.requires_agents:` (`conversation_engine.py:212`) — calls
   `travel_manager.execute(...)`. Per `ai/concierge/decision_engine.py`'s
   `_AGENT_MAP`, this branch is the live dispatcher for `MODIFY_TRIP`
   (`flight_agent`, `hotel_agent`), `DESTINATION_QUESTION`
   (`experience_agent`), `TRAVEL_ADVICE` (`experience_agent`), and
   `BUDGET_ADVICE` (`budget_agent`).

This is independently confirmed by an existing, passing test:
`services/api/tests/test_trip_brain_routing.py::test_modify_trip_still_uses_legacy_travel_manager_path`.

Tracing the dependency chain: `TravelManager` (`ai/manager/travel_manager.py`)
imports `AgentRegistry`/`default_registry` (`ai/registry/agent_registry.py`),
which imports and registers all five agent classes
(`ai/agents/{budget,experience,flight,hotel,visa}_agent.py`). Every one of
these files is reachable, at runtime, from a live, tested, currently-shipping
conversation intent. None of it is dead code — it was never made "uncalled"
by T-022; T-022 only bypassed it for `PLAN_TRIP`.

**Also verified, not part of this legacy chain:** the `recommended_agents`
field returned by `POST /conversation/message` (populated from
`decision.requires_agents`, computed by `_AGENT_MAP` for every intent
including `PLAN_TRIP`) and the `recommended_agents` field on each Discovery
module's own response schema (`ai/discovery/*/​*_intelligence.py`, a static
informational string unrelated to whether `TravelManager` actually runs) are
both separate, intentional, tested pieces of the public API contract
(`services/api/tests/test_conversation.py`,
`services/api/tests/test_trip_brain_routing.py::test_plan_trip_response_includes_recommended_agents_field_for_rollback_visibility`).
Neither is legacy orchestration and neither is touched by this ADR.

One genuinely dead artifact was found: `TravelManager.list_agents()`
(`ai/manager/travel_manager.py:66-67`) has zero callers anywhere in the
repository (its only caller would be `default_registry.list_agents()`
directly, which the registry's own tests already call without going through
`TravelManager`). This is a single unused method inside an otherwise-live
class, not a file boundary — outside this task's "remove only genuinely
unused legacy orchestration **files**" scope, and left untouched to avoid
churn in code this ADR is not otherwise changing.

## Decision

**No code under `ai/manager/`, `ai/registry/`, or `ai/agents/{flight,hotel,budget,experience,visa}_agent.py`
is deleted by T-023.** Deleting it would break `MODIFY_TRIP`,
`DESTINATION_QUESTION`, `TRAVEL_ADVICE`, and `BUDGET_ADVICE` — a public
behaviour regression, which T-023's own constraints ("Preserve all public
APIs and existing behaviour," "Do not change public API behaviour")
explicitly forbid. Retiring genuinely-unused code and preserving public
behaviour are both requirements of this task; here they resolve to the same
action — leave the code in place.

**What T-023 does instead:**

1. Corrects the inaccurate "uncalled / dormant / rollback path" language in
   `ai/concierge/conversation_engine.py`'s routing comment,
   `docs/TRIP_BRAIN_ARCHITECTURE.md`'s "Relationship to Existing
   Orchestration" section, `docs/ARCHITECTURE.md`'s layer diagram and folder
   responsibilities (which had never been updated for Trip Brain at all —
   T-022 shipped without touching it), and `docs/TASK_TRACKER.md`'s T-023
   entry.
2. Records this finding as a new technical debt item
   (`docs/TECHNICAL_DEBT_REGISTER.md` TD-018) rather than a closed one — the
   legacy stack is confirmed live infrastructure, not debt scheduled for
   deletion.
3. Opens a new, distinct backlog task (T-032, unscoped and unscheduled) for
   the actual prerequisite: migrating `MODIFY_TRIP`, `DESTINATION_QUESTION`,
   `TRAVEL_ADVICE`, and `BUDGET_ADVICE` onto a real Discovery-module or Trip
   Brain equivalent path. Only once that migration ships does
   `TravelManager`/`AgentRegistry`/the five agents become genuinely unused
   and eligible for the deletion T-023 was originally asked to perform. That
   migration is a feature-shaped change (new intent handling), explicitly
   out of scope for a "do not add features" cleanup task.

No production code is deleted. No test is deleted. No public API response
shape changes.

## Alternatives Considered

| Option | Rejected Because |
|--------|-------------------|
| Delete `ai/manager/`, `ai/registry/`, the five agents as originally scoped | Breaks four live, tested conversation intents with no replacement — a direct violation of T-023's own "preserve public API behaviour" constraint |
| Delete only the `PLAN_TRIP` entry from `decision_engine.py`'s `_AGENT_MAP`, since Trip Brain makes it unreachable for dispatch | The same entry still drives the tested `recommended_agents` field in `PLAN_TRIP`'s API response (kept "for rollback visibility" per the existing test's own docstring) — removing it changes a tested public response shape for zero behavioural gain |
| Leave the inaccurate documentation as-is since no code changed | The task explicitly lists "obsolete routing or documentation references" as in scope, and the inaccurate ADR-017/architecture-doc claims are exactly the kind of drift that caused this task to be scoped incorrectly in the first place |
| Silently reduce T-023 to a no-op with no ADR | The investigation and its finding are exactly the kind of decision `docs/CODING_STANDARDS.md`/repository convention requires an ADR for — a major architecture-affecting conclusion (legacy orchestration cannot yet be retired), not a trivial change |

## Consequences

- `ai/manager/`, `ai/registry/`, and the five placeholder agents remain in
  the repository, live and load-bearing, for `MODIFY_TRIP`,
  `DESTINATION_QUESTION`, `TRAVEL_ADVICE`, `BUDGET_ADVICE`.
- `PLAN_TRIP` continues to be the only intent Trip Brain handles; this was
  already true after T-022 and is unchanged by T-023.
- The six narrow Discovery intents are untouched, as they were throughout
  T-021/T-022.
- Full legacy orchestration retirement is now correctly tracked as blocked
  on T-032 (new, unscheduled), not as "unblocked, not yet started" (its
  prior, inaccurate `TASK_TRACKER.md` status).
- `docs/TECHNICAL_DEBT_REGISTER.md` gains TD-018, documenting that the
  legacy stack is live infrastructure with a known, scoped path to removal —
  not immediate debt.
