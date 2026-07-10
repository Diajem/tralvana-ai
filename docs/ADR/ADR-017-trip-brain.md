# ADR-017: Trip Brain Architecture

**Date**: 2026-07-10
**Status**: Accepted (architecture only — no implementation in this task)
**Sprint**: 2 (T-021)

## Context

Six independent Discovery Layer modules now exist (Flight, Accommodation, Destination, Budget, Visa, Weather & Safety Intelligence — T-015 through T-020), each reachable through its own narrow `Intent` (`FLIGHT_SEARCH`, `ACCOMMODATION_SEARCH`, ...). This was the right sequencing for Epic 2 — six modules shipped independently, none blocking on the others, each fully explainable and tested in isolation.

It leaves a real gap the business objective names directly: the traveller should interact with **one** AI, Tralvana Travel, never with "Flight Intelligence" or "Visa Intelligence" by name. Today, a broad request ("plan a trip to Tokyo") does not reach any of the six real modules at all — `Intent.PLAN_TRIP` still routes through `ai/manager/TravelManager` + `ai/registry/AgentRegistry` to five Sprint-1 placeholder agents (`flight_agent`, `hotel_agent`, `budget_agent`, `experience_agent`, `visa_agent`) that return static "pending_live_data" stubs. The six real modules are only reachable one at a time, through separate narrow intents, and a traveller asking a broad question currently gets the older, weaker path.

T-021 is architecture only, per its explicit constraints: no implementation, no new APIs, no new modules, no code. This ADR records the decisions; `docs/TRIP_BRAIN_ARCHITECTURE.md`, `docs/EPIC3_ARCHITECTURE.md`, `docs/ORCHESTRATION_PATTERN.md`, and `docs/KNOWLEDGE_SOURCE_STRATEGY.md` carry the full detail each decision below points to.

## Decision

**Trip Brain is an orchestration layer above the Discovery Layer, not a seventh Discovery module and not a rewrite of any existing one.** It calls each Discovery module's existing public `service.recommend()`/`check()`/`analyse()` method — the same entrypoint `ConversationEngine` already calls for narrow intents — and does nothing else to them. The Discovery Layer pattern (`docs/DISCOVERY_LAYER_PATTERN.md`) is unchanged by this ADR in every respect.

**Trip Brain supersedes `TravelManager`/`AgentRegistry`'s role for the six domains that now have real modules, rather than being built alongside it.** The two components have the same *shape* — accept intent + context, dispatch to workers, collect results (`AgentContext` in, `list[AgentResult]` out) — but `TravelManager` currently points at placeholder agents while six real, explainable, tested modules already exist and sit unused by `PLAN_TRIP`. Keeping both paths *active* in parallel, calling different implementations of the same five-ish domains for the same live request, would be the confusing, duplicated-authority outcome this ADR exists to prevent — `PLAN_TRIP` has exactly one active dispatcher at any given time.

**Superseding the active call site is not the same as deleting the old code, and this ADR deliberately separates the two.** Implementation is split into two tasks: T-022 builds Trip Brain and repoints `PLAN_TRIP` at it, but leaves `ai/manager/TravelManager`, `ai/registry/AgentRegistry`, and the five placeholder agents in the repository, untouched and uncalled, as a fast rollback path — if Trip Brain needs to be reverted before it's proven in production, the old call site can be restored without reconstructing deleted code. T-023, a distinct task, removes the dormant legacy code once Trip Brain has been fully implemented and verified. No code is deleted by either this ADR or by T-022 itself.

**Narrow, single-domain intents keep bypassing Trip Brain entirely — this is not a regression risk, it's the design.** `FLIGHT_SEARCH`, `ACCOMMODATION_SEARCH`, `DESTINATION_DISCOVERY`, `BUDGET_ANALYSIS`, `VISA_CHECK`, and `WEATHER_ANALYSIS` continue to route directly to their one module, exactly as they do today. Trip Brain only activates for broad intents (`PLAN_TRIP` today; any future broad-planning intent later). A traveller asking one focused question should get one fast, focused answer, not a six-module fan-out they didn't ask for.

**The Coordinator resolves presentation conflicts between modules, never scoring conflicts.** When Budget Intelligence and Accommodation Intelligence disagree (backpacker-tier budget guidance vs. a 4-star top pick), Trip Brain surfaces both and states the mismatch — it never recomputes, overrides, or blends either module's score. Doing otherwise would require Trip Brain to understand domain-specific scoring logic, which is exactly the isolation the Discovery Layer pattern exists to preserve. Full detail and worked examples in `docs/ORCHESTRATION_PATTERN.md`'s Conflict Resolution section.

**Confidence propagation is second-order aggregation over values every module already produces, not a new scoring model.** Budget, Visa, and Weather Intelligence already expose an explicit `confidence` field; Flight, Accommodation, and Destination Intelligence's mean-`match_score` confidence is already computed today inside every `ConversationEngine._get_<domain>_recommendations()` method. Trip Brain's `overall_confidence = weighted_average(per_module_confidence) × completion_penalty` reuses these unchanged, applying the same weighted-sum-of-dimensions shape every Discovery module's own `SCORE_WEIGHTS` already uses, one level up.

**No new memory store.** Trip Brain reads `ai/memory/` (long-term traveller profile/DNA) and `ConversationSession` (short-term conversation state) exactly as they exist today. A within-request working context object (assembling Traveller + Goal + Trip Context once per Trip Brain pass, so five-to-six modules don't each independently re-fetch the same data) is the only new concept, and it is request-scoped and discarded afterward — not a persistent store.

**Explainability is preservation, not summarization.** Every module's own `explanation`/`reasoning` text survives into the final response verbatim, attributed to its module — `ResponseComposer._section_for()` already does this per-`AgentResult` and needs no change to keep doing it for N results instead of one. Trip Brain adds exactly one synthesis sentence naming *what* was checked, never rewriting *why* any module concluded what it did. This is a direct application of the product's own standing commitment: *"Transparent — AI decisions are explainable. The system shows why it made a recommendation, not just what it recommends"* (`docs/00-product-constitution.md`).

**Knowledge Sources, Providers, Repositories, and APIs get one precise taxonomy (`docs/KNOWLEDGE_SOURCE_STRATEGY.md`), specifically so Trip Brain cannot accidentally reach past a Discovery module's public boundary.** The single rule that falls out of it: Trip Brain only ever calls a Discovery module's public service method or reads directly from a Knowledge Source — never a Provider (which would bypass that module's scoring/reasoning/risk logic entirely) and never another module's Repository (which would recreate the tight coupling Weather Intelligence's own task explicitly ruled out, `docs/WEATHER_INTELLIGENCE_ENGINE.md`).

**Epic 3 ("Knowledge Integration") is scoped to orchestration integration only — no vector store, embeddings, or RAG.** That is Phase 5 work per `docs/ROADMAP.md`, deliberately deferred. Epic 3 defines the shape Phase 5's eventual knowledge-layer work needs to fit into (one more Knowledge Source, not a parallel system) without building any of it now — see `docs/EPIC3_ARCHITECTURE.md`.

**The Feedback Loop is named and given connection points, not built.** Every Discovery option already carries a stable, repository-persisted ID (`flight_option_id`, `visa_assessment_id`, ...) a future feedback signal could key off of with zero new ID scheme. Consumption points are named (Traveller DNA inference, each module's static `SCORE_WEIGHTS`) but neither is touched by this ADR. Full detail in `docs/ORCHESTRATION_PATTERN.md`.

## Alternatives Considered

| Option | Rejected Because |
|--------|-------------------|
| Build Trip Brain as a seventh Discovery module, with its own Provider/Normalizer/Scorer | Trip Brain has no domain of its own to score — it orchestrates six domains that already score themselves. Forcing it into the Discovery Layer pattern would be exactly the "unnecessary abstraction" this task was told to avoid |
| Keep `TravelManager`/`AgentRegistry` *actively dispatching* `PLAN_TRIP` alongside Trip Brain, both live at once | Two orchestrators pointed at overlapping domains (one real, one placeholder) both answering the same live request is the confused-authority state this ADR exists to resolve. This is distinct from the approved plan of leaving the *code* in place, uncalled, as a rollback path — only one dispatcher is ever active |
| Delete `ai/manager`/`ai/registry`/the placeholder agents in the same task that builds Trip Brain (T-022) | Removes the fastest rollback path (restoring one call site) at exactly the moment of highest risk — before Trip Brain has run against real traffic. Deferred to a distinct T-023, after T-022 is verified |
| Let the Coordinator recompute a single blended score when modules disagree | Requires Trip Brain to understand domain-specific scoring, breaking the isolation that let six modules ship independently; also actively misleading — a blended "average" of a visa requirement and a destination's appeal score is meaningless |
| Let Trip Brain call each module's Provider directly for speed | Bypasses Normalizer/Scorer/Reasoner/RiskAssessor entirely — silently discards scoring, explainability, and risk assessment, the three things every Discovery module exists to provide |
| Design and build a persistent feedback/preference-learning store now, since Trip Brain will eventually need one | Explicitly out of scope for T-021 (architecture only) and premature relative to Phase 5's roadmap sequencing — the connection points are documented so building it later doesn't require re-deriving them, without committing implementation effort now |
| Pull Phase 5's vector store/RAG work into Epic 3 since "knowledge integration" sounds related | Conflates two different jobs (orchestrating six existing modules vs. adding a new kind of knowledge source) under one name; `docs/EPIC3_ARCHITECTURE.md` exists specifically to keep them separate |

## Consequences

- `docs/TRIP_BRAIN_ARCHITECTURE.md`, `docs/EPIC3_ARCHITECTURE.md`, `docs/ORCHESTRATION_PATTERN.md`, and `docs/KNOWLEDGE_SOURCE_STRATEGY.md` are the four supporting documents this ADR summarizes; each carries full lifecycle, sequence/component diagrams, worked examples, and failure scenarios that this ADR does not duplicate.
- No code, tests, API endpoints, or existing files (beyond documentation) changed by this task — `git status` after T-021 shows only new files under `docs/`.
- `docs/DISCOVERY_LAYER_PATTERN.md` and all six Discovery module docs remain accurate and unmodified — nothing about how any of the six modules work internally changes as a result of this ADR.
- `ai/manager/TravelManager` and `ai/registry/AgentRegistry` are not deleted by this ADR, and will not be deleted by T-022 either — they are now formally identified as superseded for the six domains with real Discovery modules, and remain in place, uncalled, as T-022's rollback path until T-023 (a distinct, later task) removes them once Trip Brain is verified.
- The distinction between narrow intents (bypass Trip Brain) and broad intents (route through it) means implementing Trip Brain carries zero regression risk to the six modules' existing, tested, narrow-intent conversation paths — they are untouched by construction, not by discipline.

## Implementation Path (Not This Task)

Recorded here for continuity into the next tasks; not built as part of T-021.

- **T-022 — Build Trip Brain.** Implements this architecture exactly as documented, repoints `PLAN_TRIP` at Trip Brain instead of `TravelManager`. Does **not** touch `ai/manager/`, `ai/registry/`, or `ai/agents/{flight,hotel,budget,experience,visa}_agent.py` — they remain in the repository, uncalled, as a rollback path.
- **T-023 — Legacy orchestration cleanup.** A distinct, later task: remove `ai/manager/`, `ai/registry/`, and the five placeholder agent files, once T-022 has been fully implemented and verified. Not started until T-022 is done.

See the companion review's "Suggested Implementation Order" for T-022's phased breakdown.
