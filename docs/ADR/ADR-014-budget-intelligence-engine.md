# ADR-014: Budget Intelligence Engine

**Date**: 2026-07-10
**Status**: Accepted
**Sprint**: 2 (T-018)

## Context

T-018 adds Budget Intelligence as the fourth Discovery Layer module, built against `docs/DISCOVERY_LAYER_PATTERN.md` (ADR-011) the same way Accommodation (ADR-012) and Destination (ADR-013) Intelligence were. The backlog originally listed T-018 as Visa Intelligence Engine; the brief for this task explicitly requested Budget Intelligence instead, so it was inserted as the new T-018 and the rest of the Sprint 2/3 backlog renumbered down (`docs/TASK_TRACKER.md`, 2026-07-10 note) — Visa Intelligence is now T-019, Weather & Safety T-020, and the pre-existing Budget Optimisation Engine backlog item (cross-trip optimisation, distinct from this module) is now T-021.

Two budget-estimation components already existed: `ai.intelligence.reasoning.budget_reasoner.BudgetReasoner` (single-style estimate for Goal readiness) and `ai.planning.budget_estimator.BudgetEstimator` (single-style estimate for Trip Planning, wrapping the former with a static fallback). Neither gives the traveller a ranked, explainable comparison across budget styles — exactly the gap the Discovery Layer pattern exists to fill: "turn a category of raw options into ranked, explainable recommendations."

## Decision

**The candidate set is the five budget styles themselves**, not provider inventory. Every other Discovery module ranks options a real external provider would return (flights, hotel listings, places); Budget Intelligence has no equivalent inventory to rank — instead, `MockBudgetProvider.search()` always returns exactly five raw candidates, one per style (`backpacker`, `budget`, `balanced`, `comfort`, `luxury`), for the given destination/duration/party-size shape. This is a deliberate departure from the letter of "Provider returns raw candidate data in whatever shape a real external provider would use" (`DISCOVERY_LAYER_PATTERN.md`) but not its spirit: a real pricing-comparison provider (e.g. a multi-tier cost calculator) would return exactly this shape, and nothing downstream — Normalizer, Scorer, Reasoner, Risk Assessor, Orchestrator — needs to know the difference.

**Regional rate tables mirror `BudgetReasoner`'s existing values exactly**, rather than inventing new numbers. `MockBudgetProvider`'s `_DAILY_USD`/`_FLIGHT_USD`/`_HAUL` tables and `BudgetNormalizer`'s accommodation/food/activities/misc cost-breakdown shares are the same values already used by `ai.intelligence.reasoning.budget_reasoner.BudgetReasoner` and `ai.planning.budget_estimator.BudgetEstimator`. A Budget Intelligence option and either existing single-style estimator agree for the same style, region, and duration — "reuse existing patterns," applied to data, not just code shape. Neither existing component's public API changed.

**`cap_fit` is the dominant scoring dimension (0.40 of 1.0)**, unlike any other Discovery module's single dimension weight. The other three modules treat `budget_style` as one input among several equally-weighted concerns (interest fit, safety, transport, family suitability, ...); here, the traveller's actual budget cap (a linked Goal's `budget.max_usd`) is the entire reason this module exists. A tier that busts the cap should score low regardless of how comfortable or well-matched to style preference it otherwise is — `cap_fit` decays linearly from 1.0 (well under cap) through 0.5 (exactly at cap) to 0.0 (100%+ over cap), and with no cap supplied falls back to a neutral 0.6, the same "no input, no penalty" convention used by `season_fit`/`interest_fit` defaults elsewhere in the Discovery Layer.

**Reasoner class named `BudgetOptionReasoner`, not `BudgetReasoner`**, despite living in a same-named `budget_reasoner.py` file per the Discovery Layer's `<domain>_reasoner.py` convention. `ai.intelligence.reasoning.budget_reasoner.BudgetReasoner` already exists at a different module path with no import collision, but keeping the class names distinct avoids "which `BudgetReasoner`?" ambiguity in code review, stack traces, and `grep` output. The Provider, Normalizer, Scorer, Risk Assessor, and Orchestrator classes (`MockBudgetProvider`, `BudgetNormalizer`, `BudgetScorer`, `BudgetRiskAssessor`, `BudgetIntelligence`) have no such collision and keep the standard naming.

**Six recommendation types, not the seven-or-nine of Accommodation/Destination.** With exactly five style candidates, `AVOID` → `BEST_OVERALL` → `LOWEST_COST` (module-specific objective winner, mirroring Flight's `LOWEST_PRICE`) → `MOST_COMFORTABLE` (second objective winner) → `BEST_VALUE`/`BEST_FOR_FAMILY` (two persona categories) gives exact 1:1 coverage in the common case where no tier is avoided — more categories than that would either force duplicate-worthy distinctions on a 5-candidate set or sit unused. The same `persona_score >= 0.45` relevance floor introduced in Destination Intelligence (ADR-013) applies to `BEST_VALUE`/`BEST_FOR_FAMILY`, and the same guaranteed-coverage fallback handles the AVOID-reduces-the-pool edge case.

**Family suitability is a tier-intrinsic score, not blended with affordability.** `family_suitability_score` reflects whether a tier's implied travel style suits children (comfort/balanced score highest, backpacker lowest) independent of whether that tier fits the traveller's budget — the same separation of concerns as Destination Intelligence's `family_score` being independent of `budget_score`. This means `BEST_FOR_FAMILY` can legitimately land on a tier the traveller can't actually afford (its `reasoning` states the cap overage explicitly, same honesty mechanism as every other over-cap option) — consistent with `MOST_COMFORTABLE` not claiming to be cheap either. The alternative (blending affordability into the family persona score) would make `BEST_FOR_FAMILY` a second `BEST_VALUE` in practice, collapsing two distinct signals into one.

## Alternatives Considered

| Option | Rejected Because |
|--------|-------------------|
| Rank real provider-shaped budget "packages" instead of the five abstract styles | No existing provider or data source in this codebase models discrete budget packages; the five styles are already the established vocabulary across Flight/Accommodation/Destination Intelligence's `budget_style` field, so reusing them as the candidate set requires no new taxonomy |
| Invent new regional rate numbers for `MockBudgetProvider` | Would make a Budget Intelligence option and a `BudgetReasoner`/`BudgetEstimator` estimate disagree for the same inputs — confusing and inconsistent with "reuse existing patterns" |
| Blend cap overage into `RiskAssessor` instead of `Scorer` | Cap fit is a preference-dependent judgement (depends on the *traveller's own* cap), and every other Discovery module's Risk Assessor is explicitly property-intrinsic only, taking no preferences parameter — keeping that invariant means cap-driven AVOID labelling belongs in scoring, not risk assessment |
| Fold `BEST_VALUE`/`BEST_FOR_FAMILY` affordability together into one persona | Loses the distinct "who is this actually good value for" vs. "who is this suitable for" signals; five candidates comfortably support two independent personas without over-fitting |
| Keep the Reasoner class named `BudgetReasoner` | No hard collision (different module path), but real ambiguity risk in review/debugging given `ai.intelligence.reasoning.budget_reasoner.BudgetReasoner` already exists and does something meaningfully different |

## Consequences

- Budget Intelligence is the fourth reference implementation in `docs/DISCOVERY_LAYER_PATTERN.md`, alongside Flight (ADR-010), Accommodation (ADR-012), and Destination (ADR-013).
- `docs/TASK_TRACKER.md` backlog renumbered: Budget Intelligence is now T-018; Visa Intelligence T-019; Weather & Safety T-020; the pre-existing (and functionally distinct) Budget Optimisation Engine backlog item is now T-021; Sprint 3 items shifted from T-021–T-027 to T-022–T-028.
- 78 new tests (mock provider determinism, normalizer, scorer, risk assessor, orchestrator, API endpoints, conversation routing, intent/decision coverage) — 367 total, all passing. Zero regressions to Flight, Accommodation, or Destination Intelligence, and zero changes to `BudgetReasoner`/`BudgetEstimator`'s existing behaviour.
- A new `Intent.BUDGET_ANALYSIS` sits alongside the pre-existing `Intent.BUDGET_ADVICE` — the latter still routes simple "how much does X cost" questions to the `budget_agent` specialist for a single-number answer; the former routes tier-comparison requests to this module. Verified non-colliding via `ai/tests/test_intent_classifier.py`.

## Sprint 4+ Migration Path

| Component | Upgrade |
|-----------|---------|
| `MockBudgetProvider` | Real pricing feed behind the same `search()` signature; only the Normalizer changes |
| `BudgetScorer` | Incorporate live currency-conversion and seasonal-pricing data into `cap_fit` |
| `BudgetRiskAssessor` | Live currency-volatility data instead of static heuristics |
| `BudgetRepository` | Swap for PostgreSQL adapter (same Sprint 3 migration as Goals/Trips/Flights/Accommodation/Destinations) |
| `Intent.BUDGET_ANALYSIS` | LLM-backed classification, replacing keyword patterns |
| Regional rate coverage | Expand beyond the four regional buckets (`Africa`/`Europe`/`Asia`/`Americas`) once a real pricing feed replaces static authoring |
