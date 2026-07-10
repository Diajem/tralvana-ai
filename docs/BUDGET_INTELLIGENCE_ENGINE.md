# Budget Intelligence Engine

T-018 — the fourth Discovery Layer module. Reasons about which budget tier (backpacker, budget, balanced, comfort, luxury) best fits the traveller's trip — not just a single static cost estimate.

## Architecture

```
Provider → Normalizer → Scorer → Reasoner → Risk Assessor → Recommendation → Explanation
```

| Stage | Module | Responsibility |
|-------|--------|-----------------|
| Domain | `services/api/app/domains/budget/` | BudgetOption model, REST API, in-memory repo |
| Provider | `ai/discovery/budget/mock_budget_provider.py` | Generates one raw candidate per budget style from regional rate tables |
| Normalizer | `ai/discovery/budget/budget_normalizer.py` | Raw → canonical schema; computes the full cost breakdown and 4 objective `*_score` fields |
| Scorer | `ai/discovery/budget/budget_scorer.py` | Subjective `match_score` against the traveller's budget cap, style preference, DNA, and goal type |
| Reasoner | `ai/discovery/budget/budget_reasoner.py` (`BudgetOptionReasoner`) | Human-readable explanation from the score breakdown |
| Risk Assessor | `ai/discovery/budget/budget_risk_assessor.py` | Per-option risk flags |
| Orchestrator | `ai/discovery/budget/budget_intelligence.py` | Wires the above together, ranks, labels |
| Conversation | `ai/concierge/conversation_engine.py` | Routes `BUDGET_ANALYSIS` intent directly to this engine |

See `docs/DISCOVERY_LAYER_PATTERN.md` for the general pipeline; this module follows it exactly, same as Flight (ADR-010), Accommodation (ADR-012), and Destination (ADR-013) Intelligence.

## The Candidate Set Is the Five Budget Styles

Unlike the other three Discovery modules, Budget Intelligence doesn't rank provider inventory (flights, hotels, places) — it ranks the five budget styles already used as a preference input elsewhere in the codebase (`backpacker`, `budget`, `balanced`, `comfort`, `luxury`) as first-class candidates for one specific trip shape (destination, duration, party size). `MockBudgetProvider.search()` always returns exactly five raw candidates, one per style.

**Why not just pick the traveller's stated style directly?** Because the traveller's stated `budget_style` is a starting preference, not a hard constraint — Budget Intelligence shows how every tier actually performs against their real budget cap (from a linked Goal's `budget.max_usd`) and explains the trade-offs, the same way Flight Intelligence doesn't just book the traveller's preferred cabin class but ranks alternatives too.

## Relationship to Existing Budget Components

Two budget-estimation components already existed before this module:

- **`ai.intelligence.reasoning.budget_reasoner.BudgetReasoner`** — a single-style cost estimate keyed to knowledge-graph country/continent data, used for Goal readiness scoring.
- **`ai.planning.budget_estimator.BudgetEstimator`** — a single-style cost estimate for Trip Planning, tries `BudgetReasoner` first and falls back to static global tables.

Both answer "what will this trip cost at my chosen style?" — a single number. Budget Intelligence answers "which style should I choose, and why?" — a ranked, explainable comparison across all five. `MockBudgetProvider`'s regional daily-rate and flight-cost tables use the **same values** as `BudgetReasoner`'s `_DAILY_USD`/`_FLIGHT_USD`/`_HAUL`, and the cost-breakdown shares (accommodation/food/activities/misc) match `BudgetEstimator`'s, so a Budget Intelligence option and either existing estimator agree for the same style, region, and duration. Nothing about `BudgetReasoner` or `BudgetEstimator`'s public API changed — both are still used exactly as before by Goal readiness scoring and Trip Planning.

The Reasoner class is named `BudgetOptionReasoner`, not `BudgetReasoner`, specifically to avoid confusion with `ai.intelligence.reasoning.budget_reasoner.BudgetReasoner` despite living in a same-named `budget_reasoner.py` file (the Discovery Layer's `<domain>_reasoner.py` naming convention).

## BudgetOption Fields

| Field | Type | Description |
|-------|------|-------------|
| `budget_option_id` | str | UUID |
| `traveller_id` / `trip_id` | str \| None | Linked traveller / trip |
| `destination` / `region` | str | Location context (`region` is the internal rate-table bucket, not a display region) |
| `budget_style` | str | One of the 5 styles below |
| `duration_days` / `adults` / `children` | int | Trip shape |
| `cabin_class` | str | Implied flight cabin for this style (`economy`/`business`/`first`) |
| `daily_cost_usd` / `flight_cost_usd` / `accommodation_usd` / `food_usd` / `activities_usd` / `misc_usd` / `total_cost_usd` | int | Full cost breakdown, USD |
| `cost_per_day_usd` / `cost_per_person_usd` | int | Derived convenience fields |
| `currency` | str | Always `"USD"` in Sprint 1 |
| `affordability_score` / `comfort_score` / `cost_certainty_score` / `family_suitability_score` | float | 0.0–1.0, objective (Normalizer) |
| `match_score` | float | 0.0–1.0, subjective (Scorer) |
| `reasoning` | str | Explanation of the score |
| `risks` | list[str] | Per-option risk flags |
| `assumptions` | list[str] | Per-option assumptions |
| `recommendation_type` | str | One of the 6 types below |

## Budget Styles

`backpacker`, `budget`, `balanced`, `comfort`, `luxury` — ordered from leanest to most premium. Each style implies a flight cabin class (`backpacker`/`budget`/`balanced` → economy, `comfort` → business, `luxury` → first) and a regional daily per-person rate, identical to the existing `BudgetReasoner` tables.

## Recommendation Types

Same priority-ordered, exhaustive labelling algorithm as the other three Discovery modules:

1. **AVOID** — `match_score < 0.35`, in practice almost always a tier whose `total_cost_usd` badly exceeds the traveller's budget cap
2. **BEST_OVERALL** — highest score among the rest
3. **LOWEST_COST** — cheapest remaining `total_cost_usd`
4. **MOST_COMFORTABLE** — highest remaining `comfort_score`
5. **BEST_VALUE / BEST_FOR_FAMILY** — two persona-weighted sub-scores each claim their best-fit remaining option, subject to the same `persona_score >= 0.45` relevance floor introduced in Destination Intelligence (ADR-013)
6. Guaranteed-coverage fallback — any option still unlabelled falls back to its own best-fit persona

With exactly five candidates and up to five non-AVOID categories, coverage is exact in the common case (no tier avoided); the AVOID and fallback rules handle the rest, same as the other Discovery modules.

## Scoring

`BudgetScorer` computes four weighted, independently explainable dimensions (weights sum to 1.0): `cap_fit` (0.40), `style_fit` (0.25), `affordability_fit` (0.20), `family_fit` (0.15).

**`cap_fit` carries the most weight** because staying within the traveller's actual budget is the entire point of this module — the other three Discovery modules treat `budget_style` as one input among several; here it defines the candidate set itself, so the traveller's hard cap (from a linked Goal's `budget.max_usd`) has to dominate. Under the cap, `cap_fit` scales up to 1.0 the further under cap the option sits; over the cap, it decays linearly and reaches 0.0 once the option is 100% over budget. No cap supplied → neutral 0.6 baseline, same convention as `season_fit`/`interest_fit`'s neutral defaults elsewhere in the Discovery Layer.

**`style_fit`** rewards proximity to the traveller's stated preferred style on the 5-point style ordering (exact match 1.0, one step away 0.7, two steps 0.45, three steps 0.25, four steps 0.1).

A DNA/goal-type adjustment layer (±0.05–0.08) follows: `budget_consciousness` boosts leaner tiers, `luxury_orientation`/`business_orientation` boost comfort/luxury tiers, `family_orientation` boosts family-suitable tiers, and goal types (`BUSINESS_TRAVEL`, `FAMILY_TRIP`, `ROMANTIC_TRIP`/`RELAXATION`, `ADVENTURE`) each nudge toward the tier that best matches that kind of trip. Every adjustment is logged in `dna_notes` and surfaces in `reasoning`.

## Risk Assessment

Property-intrinsic only, matching the pattern used by every other Discovery module's Risk Assessor — whether a tier exceeds the *traveller's own* cap is a preference-dependent judgement and lives in `BudgetScorer`'s `cap_fit` (and ultimately the AVOID label), not here. Flags: low cost-certainty tiers (`backpacker`/`luxury`), high absolute cost (`> $5,000`), backpacker-tier informal accommodation/transport, trips over 21 days (currency/price-drift exposure), and backpacker tier with children present.

## Conversation Integration

A new `Intent.BUDGET_ANALYSIS` was added, checked before `PLAN_TRIP` and before the pre-existing `Intent.BUDGET_ADVICE` (patterns: `"recommend a budget"`, `"compare budget options"`, `"budget plan for"`, etc. — verified not to collide with `BUDGET_ADVICE`'s `"how much does it cost"`/`"how expensive"`/`"affordable hotels"` triggers, which continue routing to the pre-existing `budget_agent` specialist for a simpler single-number answer).

Like `DESTINATION_DISCOVERY`, `BUDGET_ANALYSIS` is **always ready** — no destination is required, since comparing tiers at default global-average rates is itself a useful answer. `DecisionEngine` maps it to zero specialist agents; `ConversationEngine._get_budget_recommendations()` calls the service directly, matching Flight, Accommodation, and Destination Intelligence.

## Constraints

- No live pricing feeds, no booking, no payment
- Deterministic mock data only — same inputs always produce the same five candidates and costs
- Sprint 4+: swap `MockBudgetProvider` for a real pricing feed; only the Normalizer changes
