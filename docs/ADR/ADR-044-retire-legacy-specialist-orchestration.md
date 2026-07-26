# ADR-044: Retire Legacy Specialist Orchestration

**Status:** Accepted

**Date:** 2026-07-26

**Task:** T-032

## Context

Trip Brain replaced the Sprint-1 `TravelManager` path for `PLAN_TRIP` in
T-022, but four conversation intents still executed placeholder agents:

- `MODIFY_TRIP`
- `DESTINATION_QUESTION`
- `TRAVEL_ADVICE`
- `BUDGET_ADVICE`

Those agents returned static, future-sprint messaging even though Tralvana
already had real Destination and Budget Intelligence services and a complete
Trip Brain. ADR-018 correctly kept the legacy files while those routes were
still live and made their migration the prerequisite for deletion.

## Decision

- Route `DESTINATION_QUESTION` and `TRAVEL_ADVICE` directly to Destination
  Intelligence.
- Route `BUDGET_ADVICE` directly to Budget Intelligence.
- Route `MODIFY_TRIP` through Trip Brain after merging the active
  conversation's planning entities, Trip ID, and latest-recommendation
  destination with entities from the new message.
- Require both an existing trip/destination and an explicit change before a
  modification runs. Ask focused clarification questions when either is
  absent.
- Keep the public `recommended_agents` response field, but populate it with
  real capability names (`destination_intelligence`, `budget_intelligence`,
  or `trip_brain`) rather than deleted placeholder-agent names.
- Delete `ai/manager/`, `ai/registry/`, the five placeholder agents under
  `ai/agents/`, and their registry-only tests.
- Replace obsolete Sprint-number availability promises with a source-aware
  estimate notice.
- Enforce retirement with an automated production-tree scan that rejects
  imports of `ai.manager`, `ai.registry`, or `ai.agents`.

## Consequences

- Every live conversation intent now uses Trip Brain, a focused Discovery
  service, Explainability, profile handling, or direct conversation logic.
- Trip changes preserve the existing `trip_id` and use current session
  context rather than starting an unrelated placeholder response.
- A standalone ambiguous change request fails safely into clarification.
- The dormant rollback stack is gone; rollback is available through Git
  history rather than duplicate production implementations.
- The Discovery modules' own informational `recommended_agents` fields remain
  separate public-contract data and are not executable registries.

## Rejected alternatives

### Keep the legacy stack as a permanent fallback

Rejected because the real replacement paths are now covered end to end.
Keeping two implementations would restore ambiguous authority and allow the
placeholder output to drift further.

### Treat every modification as a new trip

Rejected because it would lose the conversation's Trip ID, planning facts,
and latest recommendation, breaking multi-turn continuity.

### Send all advice through Trip Brain

Rejected because a destination or budget question needs only one focused
Discovery capability. Running the full planner would add unnecessary work and
unrelated output.
