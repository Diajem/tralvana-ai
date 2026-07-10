# Orchestration Pattern

T-021 — architecture only. The general pattern for coordinating multiple Discovery modules behind one traveller-facing response. Trip Brain (`docs/TRIP_BRAIN_ARCHITECTURE.md`) is this pattern's first and, for now, only reference implementation — the same relationship `docs/DISCOVERY_LAYER_PATTERN.md` has to its six Discovery modules.

## The Pattern

```
Planner → Coordinator → { Discovery Modules ⇄ Knowledge Sources } → Response Composer
                                      ↓
                                    Memory
                                      ↓
                                Feedback Loop (future)
```

Seven components. Five already exist and are reused unmodified. Two (Coordinator, and the not-yet-built Feedback Loop) are new or future.

## Planner

**Role**: Turn raw traveller input into a structured decision about what's being asked and whether there's enough information to act on it.

**Existing implementation, reused unmodified**: `ai/concierge/intent_classifier.py` (`IntentClassifier`) + `ai/concierge/decision_engine.py` (`DecisionEngine`). Together they already do exactly this: classify intent, extract entities, and decide `has_enough_information` / `follow_up_questions` / `is_safety_sensitive` / `requires_live_data`. Six Discovery modules' worth of intents (`FLIGHT_SEARCH` through `WEATHER_ANALYSIS`) already flow through this exact Planner today.

**What Orchestration adds**: nothing to the Planner itself. The Coordinator (below) is a new *consumer* of the Planner's output for broad intents — the Planner does not need to know Trip Brain exists.

## Coordinator

**Role**: Given the Planner's output plus assembled context, decide which Discovery modules are relevant, run them, merge their results, resolve conflicts between them, and produce one unified result.

**New**: this is Trip Brain's core (`TripBrain` in the proposed `ai/trip_brain/` package — see the companion review for the folder structure). No equivalent exists today. The nearest prior art is `ai/manager/TravelManager`, which coordinates the five placeholder specialist agents via `AgentRegistry` — architecturally the same *shape* (accept an intent + context, dispatch to workers, collect `AgentResult`s), but pointed at the wrong workers (placeholders instead of the six real Discovery modules). The Coordinator pattern described here supersedes `TravelManager`'s *active* role for the six domains that now have real Discovery modules — see ADR-017 for why this is a supersession, not a rewrite from scratch (the dispatch shape, `AgentContext` in, `list[AgentResult]` out, is kept), and for why superseding the call site (T-022) and removing the now-dormant `TravelManager`/`AgentRegistry` code (T-023, later, after T-022 is verified) are deliberately separate tasks, not one.

**Coordinator sub-responsibilities**, each mapped to a Trip Brain lifecycle stage in `docs/TRIP_BRAIN_ARCHITECTURE.md`:

- Module selection ("Determine Required Intelligence Modules")
- Parallel execution ("Run Required Modules")
- Merge ("Merge Results")
- Conflict resolution ("Resolve Conflicts") — see below
- Confidence aggregation ("Confidence Calculation")

### Conflict Resolution, in Detail

Two Discovery modules can legitimately disagree, because each reasons over a different slice of the same trip:

| Conflict | Example | Resolution rule |
|---|---|---|
| Budget tier vs. Accommodation pick | Budget Intelligence's `BEST_OVERALL` is `backpacker`; Accommodation Intelligence's `BEST_OVERALL` is a 4-star hotel | Do not silently override either. Surface both; state the mismatch as an assumption ("Your best-value accommodation pick is above your backpacker-tier budget guidance — consider the `BEST_FOR_BUDGET`-labelled accommodation option instead"). Never mutate one module's output to agree with another's — that would fabricate a recommendation neither module actually produced. |
| Weather vs. requested month | Traveller asked for July; Weather Intelligence's alternative-months data shows March scores much higher | Already handled *inside* Weather Intelligence's own `explanation`/`alternative_months` (`docs/WEATHER_INTELLIGENCE_ENGINE.md`) — the Coordinator does not need its own logic here, it just passes the module's own trade-off framing through unchanged. |
| Visa risk vs. Destination pick | Destination Intelligence ranks a neighbourhood highly; Visa Intelligence returns `VISA_REQUIRED` with a long processing time | Not a scoring conflict — both are correct within their own domain. The Coordinator's job is sequencing in the response, not resolution: lead with the fact that matters most for planning (visa processing time is a hard constraint; destination appeal is not) — a composition decision for `Response Composer`, not a data-merging decision for the Coordinator. |

The general rule: **the Coordinator resolves *presentation* conflicts (what to say first, what to flag), never *scoring* conflicts (whose number is right).** No module's score, ranking, or label is ever recomputed, overridden, or blended by the Coordinator — doing so would require Trip Brain to understand domain-specific scoring logic, which is exactly the responsibility the Discovery Layer pattern keeps isolated per module.

## Discovery Modules

**Role**: Produce ranked, explainable options (or, for Visa/Weather, one explainable assessment) within one domain.

**Existing implementation, entirely unchanged**: the six modules under `ai/discovery/` plus their `services/api/app/domains/<domain>/` API layers, per `docs/DISCOVERY_LAYER_PATTERN.md`. The Coordinator calls each module's existing public service method — `flight_intelligence_service.recommend(...)`, `visa_intelligence_service.check(...)`, `weather_intelligence_service.analyse(...)`, etc. — exactly as `ConversationEngine` already does for narrow intents today. No Discovery module gains an awareness of the Coordinator; from inside `ai/discovery/flights/`, being called by the Coordinator and being called directly by `ConversationEngine` are indistinguishable.

## Knowledge Sources

**Role**: Shared factual and inferred context every Discovery module (and the Coordinator itself) reads, as opposed to domain-specific candidate data (that's a Provider's job — see `docs/KNOWLEDGE_SOURCE_STRATEGY.md` for the precise boundary).

**Existing implementation, reused unmodified**: `ai/intelligence/` (knowledge graph, ontology, reasoning engines, traveller DNA) and `ai/memory/` (traveller profile). Every Discovery module's Scorer already reads Traveller DNA for its adjustment layer; the Coordinator reads the same source once, up front, as part of building Traveller Context, rather than each module independently re-deriving it mid-request. Full taxonomy in `docs/KNOWLEDGE_SOURCE_STRATEGY.md`.

## Response Composer

**Role**: Turn one or more structured results into one coherent traveller-facing message.

**Existing implementation, reused and extended (additively)**: `ai/concierge/response_composer.py`. Already multi-result-ready — `compose()` already accepts `results: list[AgentResult]` and iterates `_section_for()` over each, and `ConversationEngine._build_output()` already concatenates `assumptions`/`missing_information`/`next_actions` across multiple results. The only extension needed is a synthesis preamble for the multi-module case (see `docs/TRIP_BRAIN_ARCHITECTURE.md`'s Explainability Strategy) — every other piece of `ResponseComposer` already works for N results, because it was written generically even though only ever exercised with N=1 until now.

## Memory

**Role**: Carry traveller identity, preferences, and conversation state across turns and requests.

**Existing implementation, reused unmodified**: `ai/memory/` (long-term) and `ConversationSession` (short-term, per-conversation). No new memory store. Full detail in `docs/TRIP_BRAIN_ARCHITECTURE.md`'s Memory Usage section.

## Feedback Loop

**Role**: Let traveller reactions to recommendations — accepted, rejected, modified, eventually booked — improve future recommendations.

**Status: does not exist today, anywhere in the codebase.** This section is architecture for a *future* capability, explicitly not built as part of T-021, and not required for Trip Brain to function — Trip Brain works correctly with zero feedback loop, exactly as every Discovery module works correctly today with static, never-adapting `SCORE_WEIGHTS`.

**Where it would connect, when built**:

1. **Signal capture** — every Discovery option already carries a stable ID (`flight_option_id`, `destination_option_id`, `budget_option_id`, ...) persisted via its domain's repository. A future feedback event ("traveller created a Trip from `flight_option_id=X`") is naturally keyed to data that already exists — no new ID scheme required.
2. **Signal storage** — a new, small domain (not a Discovery module) recording `(traveller_id, option_id, module, action)` tuples. Out of scope for T-021; a candidate for a future task, not this one.
3. **Signal consumption** — two existing extension points, unchanged in shape: `ai/intelligence/traveller_dna/dna_classifier.py`'s trait inference (today derived only from profile fields — could one day also weight in accepted/rejected options) and each Discovery module's `SCORE_WEIGHTS` constants (today static — could one day be traveller-adjusted). Both are named explicitly in `docs/ROADMAP.md` Phase 5 as "preference learning."

The Feedback Loop is documented here for completeness because the task asked for it, and because naming the connection points now (rather than inventing them later under time pressure) is cheap. Building it is explicitly **not** part of what should become T-022 — see the companion review.

## Reference Implementation

| Component | Reference Implementation | Status |
|---|---|---|
| Planner | `IntentClassifier` + `DecisionEngine` | Existing, reused |
| Coordinator | Trip Brain (`docs/TRIP_BRAIN_ARCHITECTURE.md`) | Architecture defined (T-021); not yet built |
| Discovery Modules | Flight, Accommodation, Destination, Budget, Visa, Weather Intelligence | Existing, reused |
| Knowledge Sources | `ai/intelligence/`, `ai/memory/` | Existing, reused |
| Response Composer | `ai/concierge/response_composer.py` | Existing; minor additive extension needed |
| Memory | `ai/memory/`, `ConversationSession` | Existing, reused |
| Feedback Loop | — | Not built; connection points identified only |
