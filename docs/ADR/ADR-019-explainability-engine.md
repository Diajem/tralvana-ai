# ADR-019: Explainability Engine

**Date**: 2026-07-11
**Status**: Accepted
**Sprint**: 2 (T-024)

## Context

Six Discovery modules and Trip Brain (T-015–T-022) already produce
reasoning at every level — a Reasoner's `explain()` text per option, a
Risk Assessor's flagged risks, a Normalizer's assumptions about missing
input, and Trip Brain's own second-order confidence aggregation and
conflict detection (`docs/TRIP_BRAIN_ARCHITECTURE.md`). This reasoning is
preserved and merged, but it is scattered across `AgentResult.data`,
`.assumptions`, `.risks`, and one synthesis sentence — there was no
single place that turned it into direct answers to the questions a
traveller actually asks: why this option, why not a cheaper one, what was
assumed, what risks mattered, what would change the answer, and how
confident the system is (`docs/00-product-constitution.md`'s standing
transparency commitment).

T-024 builds that place: a shared Explainability Engine that reuses
existing reasoning only.

## Decision

**The Explainability Engine is a presentation layer over existing
reasoning, not an eighth intelligence engine.** It has no domain of its
own to score. It reads `AgentResult` fields and `UnifiedRecommendation`
fields that Discovery modules and Trip Brain already produce, and returns
a structured dict — never a new score, never a re-ranking, never new
travel logic. This is the same architectural move ADR-017 made for Trip
Brain relative to the Discovery Layer, one level up.

**It sits in the pipeline exactly where the architecture brief places
it**: `Discovery Modules → Trip Brain → Explainability Engine → Response
Composer → Traveller`. `ai/trip_brain/coordinator.py`'s `TripBrain.plan()`
calls it once, immediately after conflict resolution and confidence
aggregation, and attaches the result to
`UnifiedRecommendation.explanation`. This means every `PLAN_TRIP` request
computes its explanation once, at plan time — callers (the conversation
follow-up path, `POST /explain`) reuse it rather than recomputing.

**Trade-off detection reads labels each Discovery module's own algorithm
already assigns, extended with one new field.**
`docs/DISCOVERY_LAYER_PATTERN.md`'s labelling algorithm already computes
`LOWEST_PRICE` (flight), `BEST_BUDGET` (accommodation), and `LOWEST_COST`
(budget) labels among ranked options — the Trip Brain adapters
(`ai/trip_brain/discovery_adapters.py`) previously discarded everything
but the `BEST_OVERALL` pick (`top_option`). A new `alternative_option` key
on `AgentResult.data` surfaces the module's own cheapest-labelled option
alongside it, letting `tradeoff_analyser.py` compare "what was
recommended" against "the cheaper option that wasn't" using only fields
already computed. No score changes; `top_option` selection is untouched.

**Confidence explanation reasons are read from existing assumption text,
not a new taxonomy.** `assumption_explainer.categorize()` matches known
phrasing every Discovery module already uses ("No traveller profile
linked...", "...deterministic mock data...") against three categories
(missing traveller information, mock/incomplete provider data, unknown
destination or rule). This is a read of existing conventions across the
six modules, not new domain knowledge.

**Presentation conflicts Trip Brain already detects are captured, not
re-derived.** `ai/trip_brain/conflicts.py`'s `detect_conflicts()` return
value was previously discarded by the Coordinator (only its side effect —
appending a note to one module's assumptions — was kept).
`UnifiedRecommendation` gained a `conflicts: list[str]` field so the
Explainability Engine surfaces them as trade-offs without recomputing
anything.

**`EXPLAIN_RECOMMENDATION` reuses the conversation's cached Trip Brain
result rather than re-running it.** `ConversationSession` gained
`last_recommendation: UnifiedRecommendation | None`, populated only when
`PLAN_TRIP` routes through Trip Brain — matching this task's scope
literally ("Reuse the latest Trip Brain result in the conversation
session"). Narrow, single-module intents (`FLIGHT_SEARCH`, etc.) do not
populate it; asking "why?" right after a narrow-intent answer gets the
same "nothing to explain yet" fallback as a brand-new conversation. This
is a deliberate scope boundary, not an oversight — extending it to narrow
intents is straightforward future work if needed, but was not asked for.

**`EXPLAIN_RECOMMENDATION`'s response text bypasses `ResponseComposer.compose()`
— the one deviation from the literal architecture diagram, made for a
concrete, testable reason.** `compose()`'s `_section_for()` loop renders
one full section per `AgentResult` in `results`. Reusing it for a
follow-up (passing the same `results` Trip Brain already produced) means
every module's full section — Flights, Accommodation, Destination,
Budget, Visa, Weather — gets rendered again beneath the actual answer, on
every single follow-up question. A traveller asking "how confident are
you?" would get a one-line answer buried under a repeat of the entire
original `PLAN_TRIP` response. `ExplainabilityEngine.answer_question()`
is used instead — it is itself a minimal, deterministic composer (it only
selects and formats fields the explanation dict already contains, never
generating new content) scoped specifically to this intent.
`ResponseComposer` itself is unmodified and every other intent — all six
narrow intents, `PLAN_TRIP`, and the four legacy-`TravelManager` intents —
routes through it exactly as before. `results` is still passed to
`_build_output()` so assumptions/missing information continue to populate
the JSON envelope; only the chat text itself bypasses `compose()`.

**No new persistent model.** `explain()` returns a plain `dict[str, Any]`,
matching every other Discovery module and Trip Brain output. The one
piece of new state, `ConversationSession.last_recommendation`, is cached
in-memory exactly like every other field on that session
(`ai/concierge/conversation_engine.py`'s `_SessionStore`) — not a new
store, not a new persistence layer.

**One documented gap, not a fabricated pattern.** "Shorter trip vs. more
activities" — one of the six illustrative trade-off examples in this
task's brief — has no supporting field anywhere in the current Discovery
module output (no module exposes itinerary length or activity count).
Rather than derive a trade-off from an unrelated proxy field, this
pattern is not implemented. The five patterns that are grounded in real
fields (price vs. journey length, value vs. accommodation cost, comfort
vs. budget, visa vs. destination, weather vs. price) are implemented
exactly as specified.

## Alternatives Considered

| Option | Rejected Because |
|--------|-------------------|
| Build the Explainability Engine as a seventh/eighth Discovery-style module, with its own scoring | It has no domain of its own to score — it explains six domains that already score themselves, the same reasoning ADR-017 applied to Trip Brain |
| Recompute a blended confidence or re-rank options to produce a "best explanation" | Would require understanding domain-specific scoring, breaking the isolation Trip Brain and the Discovery Layer both depend on; also the literal T-024 constraint ("must not recalculate scores") |
| Route `EXPLAIN_RECOMMENDATION` through `ResponseComposer.compose()` unchanged, passing `results=[]` | Triggers `compose()`'s "no results" fallback (`"I'll bring in live data for flights, hotels, and pricing..."`), an unrelated and confusing message for a follow-up question |
| Route `EXPLAIN_RECOMMENDATION` through `compose()` passing the original `results` | Re-renders every module's full section on every follow-up — technically correct but poor UX, and not what any test or the product brief asked for |
| Give `EXPLAIN_RECOMMENDATION` its own new memory store keyed by conversation/trip | Explicitly out of scope ("Do not create a new persistent model unless the existing conventions require one") and unnecessary — `ConversationSession` already exists and already scopes state per conversation |
| Fabricate a "shorter trip vs. more activities" trade-off from an unrelated field (e.g. destination option count) | Would be exactly the "invented travel logic" this task's constraints forbid — a trade-off implied by data that doesn't actually support it |
| Have `POST /explain`'s `question` parameter change which fields are returned | Breaks the fixed 11-key response contract this task specifies explicitly; `question` instead only biases the `summary` field's closing sentence, keeping the shape constant |

## Consequences

- `ai/explainability/` — six new files (`explainability_engine.py`,
  `explanation_builder.py`, `confidence_explainer.py`,
  `tradeoff_analyser.py`, `assumption_explainer.py`, `risk_explainer.py`)
  plus `__init__.py`, none of which import from `ai/trip_brain/` or
  `ai/concierge/` — a strictly one-directional dependency
  (`ai/trip_brain` → `ai/explainability`, `ai/concierge` →
  `ai/explainability`), so no circular import risk.
- `ai/trip_brain/models.py` gains three additive fields on
  `UnifiedRecommendation` (`conflicts`, `explanation`, `destination`), all
  defaulted — no existing caller breaks.
- `ai/trip_brain/coordinator.py` and `ai/trip_brain/discovery_adapters.py`
  are modified additively (one new `data` key on three adapters, one new
  computed field attached at the end of `plan()`) — no module score,
  ranking, or `top_option` selection changes.
- `ai/concierge/intent_classifier.py`, `decision_engine.py`,
  `response_composer.py`, and `conversation_engine.py` gain one new
  intent (`EXPLAIN_RECOMMENDATION`) and its routing — every existing
  intent's behaviour is unchanged; regression-tested explicitly
  (`services/api/tests/test_explain_routing.py`'s
  `TestExplainRecommendationIntentRouting`).
- `services/api/app/routers/explain.py` (new) — `POST /explain`, three
  input modes, all additive to the existing API surface; no existing
  endpoint's request/response shape changes.
- `apps/web/src/app/explain/page.tsx` (new) and one additive link from
  `apps/web/src/app/trips/[id]/page.tsx` — no existing frontend page's
  behaviour changes.
- 723 tests pass (649 pre-existing + 74 new), Ruff clean, frontend
  typecheck and build clean.
