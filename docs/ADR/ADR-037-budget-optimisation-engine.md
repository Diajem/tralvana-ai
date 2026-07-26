# ADR-037: Cross-Trip Budget Optimisation

**Status:** Accepted
**Date:** 2026-07-26
**Task:** T-033

## Context

T-018 ranks five budget tiers for one trip. The remaining T-033 backlog item
requires cross-trip optimisation and removal of duplicated static estimator
paths.

The codebase had three copies or near-copies of the same estimated-rate facts:
Budget Intelligence, the Knowledge Graph Budget Reasoner, and the legacy Trip
Planner fallback. Drift was already visible in the fallback flight anchors.

## Decision

- Add `POST /budget/optimise` for 1–10 proposed trips and one USD cap.
- Reuse the existing five Budget Intelligence tiers and normaliser.
- Require each trip to declare a preferred tier, minimum tier, and priority.
- Optimise priority-weighted preference retention within the cap.
- Never select above the preferred tier or below the minimum tier.
- Return minimum-tier allocations plus an exact shortfall when infeasible.
- Use a deterministic Pareto-frontier search rather than an opaque solver.
- Extract the regional estimated-rate facts into
  `ai/discovery/budget/budget_cost_model.py`.
- Make both the mock provider and legacy Trip Planner fallback consume that
  model; preserve the Trip Planner response shape.
- Label every portfolio result `ESTIMATED_REGIONAL_RATES`.

## Consequences

- Multiple trips can be compared coherently under one budget.
- Important trips resist downgrades more strongly.
- Infeasibility is surfaced instead of silently violating minimum comfort.
- The legacy estimator and Budget Intelligence no longer maintain separate
  fallback tables.
- Some unknown-destination legacy estimates change because the canonical model
  now uses the same global haul assumptions as Budget Intelligence. This is the
  intended removal of drift.
- No live-price, booking, currency, tax, or availability capability is added.

## Rejected alternatives

| Alternative | Reason |
|---|---|
| Greedy cheapest-first downgrade | Can make a locally cheap choice that produces a worse overall priority outcome |
| Upgrade trips whenever budget remains | Spends money the traveller did not request and changes the meaning of preferred tier |
| Relax minimum tiers to force feasibility | Hides an impossible portfolio and violates explicit traveller constraints |
| Add an optimisation library | The bounded five-tier problem is deterministic and small; a new dependency adds risk without value |
| Keep the legacy static fallback tables | Preserves the cost drift T-033 is meant to remove |
