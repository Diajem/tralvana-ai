# ADR-026: Trip Assembly Engine

**Date**: 2026-07-13
**Status**: Accepted
**Sprint**: 2/3 boundary (T-040)

## Context

Through T-039, Tralvana's most sophisticated reasoning (Trip Brain
orchestrating six Discovery modules, merged and explained by the
Explainability Engine) was only reachable via `POST /conversation/message`
— a backend-only API with no frontend page. Meanwhile the *only*
frontend trip-planning experience, `/trips/new` (`POST /trips/plan`),
called `ai/planning/trip_planner.py` — Sprint 1, pre-Discovery-Layer
logic with its own budget estimator, risk assessor, and confidence
formula, entirely bypassing Trip Brain and the real Discovery modules.
T-040 asks for this to become "the primary user experience" — a
traveller describing a trip naturally and receiving one coherent
itinerary, explicitly forbidding new booking/payment logic, and
explicitly requiring that no module recalculate another's scores.

## Decision

**The Trip Assembly Engine (`ai/trip_brain/trip_assembly.py`) is a
second, separate caller of Trip Brain's output — never a change to
`ai/trip_brain/coordinator.py` itself.** `TripBrain.plan()` is
byte-for-byte unchanged; its 75+ existing tests were never at risk.
`TripAssemblyEngine.assemble()` takes an already-computed
`UnifiedRecommendation` (the exact object `coordinator.py` already
returns) plus a few context fields (`destination`, `duration_days`,
`goal_type`, `budget_style`, `interests`) and produces a
`TripItinerary`. This mirrors the relationship
`ai/concierge/conversation_engine.py` and `POST /explain`
(`services/api/app/routers/explain.py`) already have with Trip Brain —
callers of its output, not participants in producing it.

**Every section of the itinerary reads a field a Discovery module,
Trip Brain, or the Explainability Engine already computed — nothing is
recalculated.** Concretely:

| Section | Exact source | New computation? |
|---|---|---|
| Destination/Flight/Accommodation/Budget recommendation | `AgentResult.data["top_option"]` — already selected as `BEST_OVERALL` by `ai/trip_brain/discovery_adapters.py` (T-022) | No — read only |
| Visa summary / Weather expectations | `AgentResult.data` (the whole single-assessment dict) | No — read only |
| Risks / Assumptions / Why this itinerary / Confidence explanation / Alternative options | `UnifiedRecommendation.explanation[...]` — the Explainability Engine's own output | No — read only |
| Confidence | `UnifiedRecommendation.overall_confidence` | No — read only |
| Daily outline | `ai/planning/itinerary_builder.py`'s `build()` | No — called, not reimplemented (see below) |
| Executive summary | New | Yes, but templating over already-decided facts, not a new judgement (see below) |

**The daily outline reuses `ai/planning/itinerary_builder.py` (T-008,
Sprint 1) rather than building a new day-planner.** No Discovery module
produces anything resembling a morning/afternoon/evening schedule —
this genuinely didn't exist anywhere else in the codebase. Rather than
invent a new one, this task calls the existing, already-tested,
deterministic goal-type-templated builder for the first time from a
Trip-Brain-backed path (it was previously only reachable via the
legacy `trip_planner.py`). `ItineraryBuilder.build()` itself is
unmodified.

**The executive summary is a template over facts, not a new scoring
model.** `_executive_summary()` in `trip_assembly.py` builds a
paragraph from `top_option`/assessment fields that are already present
— it does not decide *which* flight or property to prefer (that's
each module's own job, unchanged); it only decides *how to phrase*
what was already decided. Every clause is conditional on the fact it
quotes actually being present (`if flight: ...`, `if visa and
visa.get("visa_status"): ...`) — a module that didn't run or came back
empty is silently omitted from the paragraph, never backfilled with an
invented claim. This satisfies "the final output should feel like an
experienced travel consultant produced it" (T-040's own framing)
without violating "no module should recalculate another module's
scores" (also T-040's own framing) — the tension is resolved by
keeping the new logic entirely in the *presentation* layer.

**`POST /planner/plan` reuses `travel_concierge.handle()` wholesale —
intent classification, goal/trip creation, and session management are
all unchanged.** The alternative (building a new one-shot endpoint
that classified intent and called Trip Brain directly, bypassing
`ConversationEngine`) would have duplicated goal/trip auto-creation
logic that already exists and is already tested. Instead, the new
router calls `travel_concierge.handle()` exactly as
`POST /conversation/message` does, then — only when
`session.last_recommendation` was populated (i.e. Trip Brain actually
ran) — fetches the Goal/Trip via the same public
`goal_service.get()`/`trip_planning_service.get()` calls
`ai/trip_brain/context.py`'s own `ContextBuilder` already makes
internally, and calls the Trip Assembly Engine. This is the smallest
possible new surface: one router, one new orchestration module, zero
changes to any existing conversation, Trip Brain, or Discovery-layer
code.

**The legacy `POST /trips/plan` (`ai/planning/trip_planner.py`) is left
running, untouched, in parallel — not migrated or removed.** It never
called Trip Brain or the real Discovery modules to begin with (a
pre-existing fact about this codebase, not something this task
changed); removing or rewriting it would be a scope expansion beyond
"preserve the existing architecture." `POST /planner/plan` is
positioned as the new, real path; `/trips/new`'s frontend page and its
backing endpoint remain exactly as they were.

## Alternatives Considered

| Option | Rejected Because |
|---|---|
| Have `TripBrain.plan()` itself build and attach the `TripItinerary` (a new field on `UnifiedRecommendation`) | Risks the 75+ existing `coordinator.py`/`UnifiedRecommendation` tests for no architectural gain — the separate-caller pattern already used by `ConversationEngine`/`POST /explain` achieves the same result with zero risk to Trip Brain's own test suite |
| Build a new daily-itinerary generator from scratch, scored against traveller preferences | Directly against "do not duplicate logic already implemented" — `ai/planning/itinerary_builder.py` already does exactly this, deterministically, and is already tested; the only reason it wasn't already wired into Trip Brain's output is that nothing had asked for it before |
| Have the executive summary re-rank or pick a "best" option itself (e.g. compare flight price vs. accommodation quality to write a more opinionated summary) | Would be exactly the kind of module-recalculation this task explicitly forbids — the summary only narrates the `BEST_OVERALL` pick each module already made |
| Build `POST /planner/plan` as a raw wrapper around `ai/trip_brain/coordinator.py` directly, bypassing `ConversationEngine` | Would duplicate goal/trip auto-creation and session bookkeeping `ConversationEngine.process()` already implements and tests; also loses multi-turn conversation continuity for free-text follow-ups |
| Retire or rewrite the legacy `/trips/plan` endpoint as part of this task | Out of scope — "preserve the existing architecture"; also risks breaking `/trips/new`'s existing frontend page and its own tests for no requirement this task actually states |

## Consequences

- New: `ai/trip_brain/trip_assembly.py`,
  `services/api/app/routers/planner.py`,
  `apps/web/src/app/planner/page.tsx`,
  `apps/web/src/types/planner.ts`, `docs/AI_TRAVEL_PLANNER.md`.
- Modified: `services/api/app/main.py` (one router registration),
  `apps/web/src/lib/api.ts` (`planTrip()`), `apps/web/src/app/page.tsx`
  (new primary CTA).
- Zero changes to `ai/trip_brain/coordinator.py`, `ai/trip_brain/models.py`,
  `ai/trip_brain/module_selection.py`, `ai/trip_brain/discovery_adapters.py`,
  `ai/trip_brain/confidence.py`, `ai/trip_brain/conflicts.py`,
  `ai/explainability/` (any file), any Discovery module's scorer/
  reasoner/risk-assessor, or `ai/planning/itinerary_builder.py` itself.
- 29 new tests (1190 total, all passing), Ruff clean, frontend
  typecheck and production build both clean.
- Verified live in a real browser: a natural-language message produced
  a complete, correctly-assembled itinerary end to end, including
  goal-type-aware daily outline enrichment.
- No booking, payment, or reservation logic exists anywhere in this
  change.

## Deferred Items

- The legacy `/trips/plan` path is not migrated to Trip Brain — left
  as a known, pre-existing parallel path, unchanged.
- No persistence of the assembled `TripItinerary` itself (it's
  recomputed per `POST /planner/plan` call from `session.last_recommendation`
  plus fresh Goal/Trip reads) — acceptable given the in-memory,
  ephemeral nature of every other store in this codebase to date.
- Executive-summary phrasing is a fixed template, not LLM-generated
  prose — consistent with every other explanation surface in this
  codebase (`ai/explainability/`), which is deliberately rule-based,
  not model-based, for auditability.
