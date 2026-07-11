# Explainability Engine

T-024 — a shared explainability layer that turns module-level reasoning
already produced by the Discovery Layer and Trip Brain into one clear,
consistent, traveller-facing explanation. See
`docs/ADR/ADR-019-explainability-engine.md` for the architectural
decisions and `docs/API_EXPLAINABILITY.md` for the HTTP contract.

## Why This Document Exists

Every Discovery module already produces reasoning — a Reasoner's
`explain()` text, a Risk Assessor's flagged risks, a Normalizer's
assumptions about missing input (`docs/DISCOVERY_LAYER_PATTERN.md`). Trip
Brain (`docs/TRIP_BRAIN_ARCHITECTURE.md`) already preserves and merges
this reasoning across up to six modules. What was missing was a single
place that turns this scattered reasoning into direct answers to the
questions a traveller actually asks:

- Why was this option recommended?
- Why was a cheaper option rejected?
- What assumptions were made?
- What risks influenced the result?
- What would change the recommendation?
- How confident is the system?

The Explainability Engine is that place. It is **not** a new intelligence
engine — it reuses existing reasoning only, and does not invent travel
logic or recalculate any Discovery module's score.

## Responsibilities

The Explainability Engine (`ai/explainability/`):

1. Accepts one or more existing module results (`AgentResult`s — Trip
   Brain's own output shape, unchanged).
2. Preserves source attribution — every driver, assumption, and risk is
   tagged with the module it came from.
3. Combines reasoning without changing its original meaning — assumptions
   and risks are deduplicated verbatim, never rewritten or summarised
   away.
4. Explains recommendation drivers, confidence, trade-offs, assumptions,
   and risks.
5. Identifies missing information and what would change the result.

It is explicitly **not** responsible for scoring, ranking, or any
domain-specific reasoning — that stays entirely inside the Discovery
Layer and Trip Brain, unchanged.

## Architecture

```
Discovery Modules → Trip Brain → Explainability Engine → Response Composer → Traveller
```

The Explainability Engine sits after Trip Brain's merge and conflict
resolution stage and before the traveller-facing text is composed
(`docs/TRIP_BRAIN_ARCHITECTURE.md`'s Orchestration Lifecycle). It reads:

- `AgentResult.data` / `.assumptions` / `.risks` / `.missing_information`
  — produced by each Discovery module's adapter
  (`ai/trip_brain/discovery_adapters.py`), unchanged.
- `UnifiedRecommendation.overall_confidence` — Trip Brain's own weighted
  aggregation (`ai/trip_brain/confidence.py`), unchanged.
- `UnifiedRecommendation.conflicts` — presentation conflicts Trip Brain's
  Coordinator already detected (`ai/trip_brain/conflicts.py`), unchanged.

It never reads a Provider or Repository directly — the same boundary rule
Trip Brain itself follows (`docs/KNOWLEDGE_SOURCE_STRATEGY.md`).

## Package Layout (`ai/explainability/`)

| File | Responsibility |
|---|---|
| `explainability_engine.py` | `ExplainabilityEngine` — the single entry point (`explain()`), and `answer_question()` for conversational follow-ups |
| `explanation_builder.py` | Recommendation drivers, alternatives considered, missing information, what-would-change, source attribution, and the one summary sentence |
| `confidence_explainer.py` | Confidence bands and the reasons a confidence value was reduced |
| `tradeoff_analyser.py` | Deterministic trade-off comparisons (price vs. journey length, comfort vs. budget, visa vs. destination, weather vs. price) |
| `assumption_explainer.py` | Verbatim, deduplicated assumption collection, plus the keyword classifier `confidence_explainer.py` reuses |
| `risk_explainer.py` | Verbatim, deduplicated risk collection, plus a plain-language note when a module failed |

## Explanation Output

`ExplainabilityEngine.explain()` returns a plain `dict[str, Any]` — no new
persistent model, consistent with every other Discovery module and Trip
Brain output in this codebase:

| Field | Contents |
|---|---|
| `summary` | One sentence naming how many modules contributed, at what confidence, optionally focused by a follow-up question |
| `recommendation_drivers` | `[{"module": ..., "driver": ...}]` — each succeeded module's own reasoning text, attributed |
| `tradeoffs` | Deterministic trade-off strings (see below), plus any Trip Brain conflicts |
| `assumptions` | Every module's assumptions, verbatim, deduplicated |
| `risks` | Every module's risks, verbatim, deduplicated, plus a note for any module that failed |
| `missing_information` | Aggregated `missing_information` fields, plus assumptions that describe a missing input |
| `confidence` | The numeric confidence explained (Trip Brain's `overall_confidence`, or the mean of succeeded modules if none is supplied) |
| `confidence_explanation` | Traveller-friendly band label plus the reasons it was reduced |
| `alternatives_considered` | Each module's labelled alternative option (if any) and why it wasn't chosen, plus a count of other options evaluated |
| `what_would_change_the_result` | Actionable suggestions derived from failed modules, missing information, and conflicts |
| `source_modules` | `[{"module": ..., "status": ...}]` for every module attempted — this is where partial failure is made visible |

## Confidence Explanation

Numeric confidence is converted into traveller-friendly language using
fixed bands:

| Range | Label |
|---|---|
| 0.90 – 1.00 | Very high confidence |
| 0.75 – 0.89 | High confidence |
| 0.60 – 0.74 | Moderate confidence |
| 0.40 – 0.59 | Low confidence |
| Below 0.40 | Very low confidence |

`confidence_explainer.explain()` never computes a confidence value — it
only labels one already produced by Trip Brain (`aggregate_confidence()`)
or a single module. Reduction reasons are read from data already present,
not invented:

- **Partial module failure** — from `modules_failed`.
- **Conflicting module results** — from `conflicts` (Trip Brain's
  `conflicts.py`).
- **Missing traveller information / mock or incomplete provider data /
  unknown destination or rule** — a keyword classifier
  (`assumption_explainer.categorize()`) reads each module's own
  assumption text for known phrasing (e.g. "No traveller profile
  linked...", "...deterministic mock data...", "...not in the mock
  catalogue..."). This is a read of existing conventions, not a new
  taxonomy — every phrase it matches already exists in a Discovery
  module's own assumption text.
- **Generic assumptions** — a fallback when assumptions exist but none
  match a known category.

## Trade-off Analysis

`tradeoff_analyser.py` compares the option Trip Brain recommended against
an alternative the same Discovery module already computed and labelled
— never a new score, never a re-ranking. Supported patterns:

| Pattern | Modules | Grounded in |
|---|---|---|
| Lower price vs. longer journey | Flight | `top_option` (`BEST_OVERALL`) vs. `alternative_option` (`LOWEST_PRICE`) — `estimated_price`, `stops`, `total_duration` |
| Better value vs. higher accommodation cost | Accommodation | `top_option` vs. `alternative_option` (`BEST_BUDGET`) — `nightly_price`, `star_rating` |
| Comfort vs. budget | Budget | `top_option` vs. `alternative_option` (`LOWEST_COST`) — `total_cost_usd`, `budget_style` |
| Visa simplicity vs. destination preference | Visa + Destination | `visa_status` not visa-free/on-arrival, and destination `match_score ≥ 0.6` |
| Ideal weather vs. peak-season price | Weather + Budget | `weather_status` favourable, and budget tier is `comfort`/`luxury` |

`alternative_option` is a new key on `AgentResult.data`, added by
`ai/trip_brain/discovery_adapters.py` (flight, accommodation, budget) —
it surfaces a labelled option (`LOWEST_PRICE` / `BEST_BUDGET` /
`LOWEST_COST`) each module's own labelling algorithm
(`docs/DISCOVERY_LAYER_PATTERN.md`) already computed, just not previously
passed to Trip Brain. No score changes; `top_option` selection is
unchanged.

**Known gap:** "shorter trip vs. more activities" (one of the illustrative
examples in T-024's brief) has no supporting field in the current
Discovery module output — no module exposes an itinerary length or
activity count. Rather than fabricate a weak signal from an unrelated
field, this pattern is not implemented. Extending `AgentResult.data` with
an activity/day-count signal is future work if this pattern is needed.

## Trip Brain Integration

`ai/trip_brain/coordinator.py`'s `TripBrain.plan()` calls
`explainability_engine.explain()` once, immediately after conflict
resolution (`detect_conflicts()`) and confidence aggregation
(`aggregate_confidence()`), and attaches the result to
`UnifiedRecommendation.explanation`. Nothing computed before that point
(scores, rankings, `results`, `overall_confidence`, `conflicts`) is
modified — the Explainability Engine only reads them.

`UnifiedRecommendation` gained three fields for this (`ai/trip_brain/models.py`):

- `conflicts: list[str]` — previously computed and discarded by the
  Coordinator (only used as a side-effect on one module's assumptions);
  now captured so the Explainability Engine doesn't have to re-derive it.
- `explanation: dict[str, Any]` — the Explainability Engine's structured
  output, computed once per `plan()` call.
- `destination: str` — carried alongside `explanation` so a caller
  re-deriving only the question-sensitive summary line
  (`services/api/app/routers/explain.py`) doesn't lose destination
  context.

Partial failure is visible in the explanation by construction: a failed
module still appears in `source_modules` with `status: "failed"`, and
`risk_explainer.py` adds a plain-language note ("X could not be
completed — that part of the recommendation is missing.") in its place —
the module's own raw exception text is never surfaced to the traveller.

## Conversation Integration

A new intent, `Intent.EXPLAIN_RECOMMENDATION`
(`ai/concierge/intent_classifier.py`), matches follow-up questions such
as "why did you recommend this?", "why not the cheaper option?", "what
assumptions did you make?", "how confident are you?", and "what would
change your answer?". Its patterns are checked before `PLAN_TRIP`,
`TRAVEL_ADVICE`, and `BUDGET_ADVICE` in `IntentClassifier._PATTERNS`,
since those intents' broader keywords ("recommend", "how much") would
otherwise swallow a follow-up question about a recommendation just made.

`ConversationSession` (`ai/concierge/conversation_engine.py`) gained one
new field: `last_recommendation: UnifiedRecommendation | None`, set only
when `PLAN_TRIP` routes through Trip Brain — narrow, single-module
intents (`FLIGHT_SEARCH`, etc.) do not populate it, matching this task's
scope ("Reuse the latest Trip Brain result"). `EXPLAIN_RECOMMENDATION`
never re-runs a Discovery module or Trip Brain: it reads
`session.last_recommendation.explanation` and calls
`ExplainabilityEngine.answer_question()`, which picks the relevant field
(trade-offs, assumptions, confidence, risks, or what-would-change) based
on a small deterministic keyword match against the question text
(`explanation_builder.focus_for_question()`) and formats it as a short
chat reply — never generating content that doesn't already exist in the
explanation dict.

**Deviation from the architecture diagram:** `EXPLAIN_RECOMMENDATION`'s
`response_text` is composed directly by
`ExplainabilityEngine.answer_question()`, not routed through
`ResponseComposer.compose()`. `compose()`'s `_section_for()` loop
re-renders every module's full section verbatim for each `AgentResult` in
`results` — reusing it for a follow-up would repeat the entire original
`PLAN_TRIP` response underneath every short answer ("why not the cheaper
option?" would return the trade-off *and* every Flights/Accommodation/
Destination/Budget/Visa/Weather section again). `results` is still passed
through to `_build_output` so assumptions/missing information from the
underlying recommendation continue to populate the JSON response
envelope — only the chat text bypasses the generic composer.
`ResponseComposer` itself is otherwise unmodified, and every other intent
still routes through it exactly as before.

If no `last_recommendation` exists yet, the traveller gets a direct
fallback: *"I don't have a recent recommendation to explain yet — ask me
to plan a trip, and I'll be able to walk you through why once I have."*

## API

See `docs/API_EXPLAINABILITY.md` for `POST /explain`'s full request/
response contract.

## Frontend

`apps/web/src/app/explain/page.tsx` — a standalone form (conversation ID
/ trip ID / optional question) rendering the full structured explanation:
drivers, trade-offs, alternatives considered, risks, assumptions, missing
information, what-could-change, and source modules with per-module status
badges. `apps/web/src/app/trips/[id]/page.tsx` links to it
(`/explain?trip_id=...`) as the practical touch point from the existing
trip-plan view, per this task's scope ("if practical" — a link, not a
duplicated fetch of Trip Brain data that page doesn't otherwise have).

## Non-Goals

- No LLM provider, no external API calls — every explanation is built
  from deterministic string templates and keyword matching, consistent
  with every other decision point in this codebase.
- No new scoring, ranking, or travel logic — every field in `explain()`'s
  output is either read verbatim or derived by simple comparison from
  data a Discovery module or Trip Brain already produced.
- No new persistent model — `explain()` returns a plain dict;
  `UnifiedRecommendation` is cached in-memory on `ConversationSession`
  exactly like the rest of that session's state, not written to a new
  store.
